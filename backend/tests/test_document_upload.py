from io import BytesIO
from pathlib import Path

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from rest_framework.test import APIClient

from documents.models import Document


UPLOAD_THROTTLE_SETTINGS = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",
        "research_run_create": "1000/min",
        "document_create": "1/min",
    },
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def temporary_media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_pdf(text: str | None = None, encrypted: bool = False) -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    if text is not None:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        font_reference = writer._add_object(font)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_reference}
                )
            }
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)

    if encrypted:
        writer.encrypt("secret")
    writer.write(output)
    return output.getvalue()


def file_error(response) -> str:
    error = response.json()["file"]
    return error[0] if isinstance(error, list) else error


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filename", "content", "expected_type"),
    [
        ("market-notes.txt", b"AI research adoption is accelerating.", "txt"),
        ("ev-market.md", b"# EV Market\n\nFleet buyers are adopting EVs.", "md"),
    ],
)
def test_upload_text_documents_creates_metadata_chunks_and_embeddings(
    api_client,
    filename,
    content,
    expected_type,
):
    response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile(filename, content)},
        format="multipart",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == Path(filename).stem
    assert body["source_type"] == "upload"
    assert body["original_filename"] == filename
    assert body["file_type"] == expected_type
    assert body["file_size"] == len(content)
    assert body["ingestion_status"] == "completed"
    assert body["ingestion_error"] == ""
    assert body["chunks"][0]["embedding"]
    assert "source_file" not in body


@pytest.mark.django_db
def test_upload_uses_non_empty_title(api_client):
    response = api_client.post(
        "/api/documents/upload/",
        {
            "title": "  Custom market title  ",
            "file": SimpleUploadedFile("ignored-title.txt", b"Market evidence"),
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Custom market title"


@pytest.mark.django_db
def test_upload_pdf_extracts_text(api_client):
    response = api_client.post(
        "/api/documents/upload/",
        {
            "file": SimpleUploadedFile(
                "market-report.pdf",
                make_pdf("PDF market evidence"),
                content_type="application/pdf",
            )
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == "pdf"
    assert "PDF market evidence" in response.json()["content"]
    assert response.json()["chunks"][0]["chunk_text"] == "PDF market evidence"


@pytest.mark.django_db
def test_duplicate_filenames_do_not_overwrite_source_files(api_client):
    first_response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("report.txt", b"First report")},
        format="multipart",
    )
    second_response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("report.txt", b"Second report")},
        format="multipart",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first, second = list(Document.objects.order_by("id"))
    assert first.source_file.name != second.source_file.name
    assert first.source_file.read() == b"First report"
    assert second.source_file.read() == b"Second report"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filename", "content", "expected_error"),
    [
        ("report.csv", b"market,data", "Unsupported file type"),
        ("invalid.txt", b"\xff\xfe", "UTF-8"),
        ("broken.pdf", b"not a pdf", "could not be read"),
        ("empty.txt", b"", "submitted file is empty"),
    ],
)
def test_invalid_uploads_return_friendly_errors_without_persistence(
    api_client,
    settings,
    filename,
    content,
    expected_error,
):
    response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile(filename, content)},
        format="multipart",
    )

    assert response.status_code == 400
    assert expected_error.lower() in file_error(response).lower()
    assert Document.objects.count() == 0
    assert not settings.MEDIA_ROOT.exists() or not any(settings.MEDIA_ROOT.rglob("*"))


@pytest.mark.django_db
@override_settings(DOCUMENT_UPLOAD_MAX_BYTES=4)
def test_upload_rejects_files_over_configured_limit(api_client):
    response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("large.txt", b"12345")},
        format="multipart",
    )

    assert response.status_code == 400
    assert "maximum upload size" in file_error(response)
    assert Document.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("content", "expected_error"),
    [
        (make_pdf(), "does not contain extractable text"),
        (make_pdf("Protected evidence", encrypted=True), "Encrypted PDF"),
    ],
)
def test_pdf_without_available_text_is_rejected(api_client, content, expected_error):
    response = api_client.post(
        "/api/documents/upload/",
        {
            "file": SimpleUploadedFile(
                "report.pdf",
                content,
                content_type="application/pdf",
            )
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert expected_error in file_error(response)
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_delete_uploaded_document_removes_source_file(api_client):
    create_response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("delete-me.txt", b"Delete this evidence")},
        format="multipart",
    )
    document = Document.objects.get(pk=create_response.json()["id"])
    source_path = Path(document.source_file.path)
    assert source_path.exists()

    delete_response = api_client.delete(f"/api/documents/{document.id}/")

    assert delete_response.status_code == 204
    assert not source_path.exists()


@pytest.mark.django_db
def test_clear_documents_removes_all_source_files(api_client):
    source_paths = []
    for filename in ("first.txt", "second.md"):
        response = api_client.post(
            "/api/documents/upload/",
            {"file": SimpleUploadedFile(filename, b"Stored market evidence")},
            format="multipart",
        )
        document = Document.objects.get(pk=response.json()["id"])
        source_paths.append(Path(document.source_file.path))

    response = api_client.delete("/api/documents/clear/")

    assert response.status_code == 200
    assert response.json()["deleted"] == 2
    assert Document.objects.count() == 0
    assert all(not path.exists() for path in source_paths)


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=UPLOAD_THROTTLE_SETTINGS)
def test_upload_uses_document_creation_throttle(api_client):
    cache.clear()
    first_response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("first.txt", b"First report")},
        format="multipart",
    )
    throttled_response = api_client.post(
        "/api/documents/upload/",
        {"file": SimpleUploadedFile("second.txt", b"Second report")},
        format="multipart",
    )

    assert first_response.status_code == 201
    assert throttled_response.status_code == 429
    assert Document.objects.count() == 1
