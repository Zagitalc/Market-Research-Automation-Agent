from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from rest_framework import serializers

from agents.services.embedding_provider import generate_embedding
from documents.models import Document
from documents.services.chunker import create_chunks_for_document
from documents.services.chunker import split_text
from documents.services.web_fetch.direct import normalize_url_for_dedup
from documents.services.web_fetch.exceptions import (
    DuplicateURLError,
    ExtractionError,
    WebFetchError,
)
from documents.services.web_fetch.factory import get_web_fetch_provider


SUPPORTED_FILE_TYPES = {
    ".txt": "txt",
    ".md": "md",
    ".pdf": "pdf",
}


def create_document_from_upload(uploaded_file: UploadedFile, title: str = "") -> Document:
    original_filename = Path(uploaded_file.name).name
    suffix = Path(original_filename).suffix.lower()
    file_type = SUPPORTED_FILE_TYPES.get(suffix)
    if not file_type:
        raise serializers.ValidationError(
            {"file": "Unsupported file type. Upload a .txt, .md, or .pdf file."}
        )

    if uploaded_file.size > settings.DOCUMENT_UPLOAD_MAX_BYTES:
        limit_mb = settings.DOCUMENT_UPLOAD_MAX_BYTES / (1024 * 1024)
        raise serializers.ValidationError(
            {"file": f"File is too large. The maximum upload size is {limit_mb:g} MB."}
        )

    content = extract_text(uploaded_file, file_type)
    if not content.strip():
        raise serializers.ValidationError(
            {"file": "The uploaded file does not contain extractable text."}
        )

    document_title = title.strip() or Path(original_filename).stem
    uploaded_file.seek(0)
    stored_file_name = ""

    try:
        with transaction.atomic():
            document = Document.objects.create(
                title=document_title,
                source_type="upload",
                source_kind=Document.SourceKind.UPLOAD,
                content=content.strip(),
                original_filename=original_filename,
                file_type=file_type,
                file_size=uploaded_file.size,
                source_file=uploaded_file,
                ingestion_status=Document.IngestionStatus.COMPLETED,
            )
            stored_file_name = document.source_file.name
            create_chunks_for_document(document)
            return document
    except Exception:
        if stored_file_name:
            document.source_file.storage.delete(stored_file_name)
        raise


def extract_text(uploaded_file: UploadedFile, file_type: str) -> str:
    uploaded_file.seek(0)
    if file_type in {"txt", "md"}:
        try:
            return uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError(
                {"file": "Text and Markdown files must use UTF-8 encoding."}
            ) from exc

    try:
        reader = PdfReader(uploaded_file)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise serializers.ValidationError(
                {"file": "Encrypted PDF files are not supported."}
            )
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    except serializers.ValidationError:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise serializers.ValidationError(
            {"file": "The PDF could not be read. Upload a valid text-based PDF."}
        ) from exc


def create_document_from_url(url: str, title: str = "") -> Document:
    try:
        normalized_requested_url = normalize_url_for_dedup(url)
        if Document.objects.filter(
            source_kind=Document.SourceKind.URL,
            source_url=normalized_requested_url,
        ).exists():
            raise DuplicateURLError()

        fetch_result = get_web_fetch_provider().fetch(url)
        normalized_final_url = normalize_url_for_dedup(fetch_result.final_url)
        if Document.objects.filter(
            source_kind=Document.SourceKind.URL,
            source_url=normalized_final_url,
        ).exists():
            raise DuplicateURLError()

        extracted_title, content = extract_html_content(fetch_result.body, fetch_result.content_type)
        clean_content = content.strip()
        if not clean_content:
            raise ExtractionError()

        document_title = title.strip() or extracted_title or fallback_title(normalized_final_url)
        chunk_rows = [
            {"chunk_text": chunk_text, "embedding": generate_embedding(chunk_text)}
            for chunk_text in split_text(clean_content)
        ]
        if not chunk_rows:
            raise ExtractionError()

        try:
            with transaction.atomic():
                if Document.objects.filter(
                    source_kind=Document.SourceKind.URL,
                    source_url=normalized_final_url,
                ).exists():
                    raise DuplicateURLError()

                document = Document.objects.create(
                    title=document_title[:255],
                    source_type="url",
                    source_kind=Document.SourceKind.URL,
                    content=clean_content,
                    source_url=normalized_final_url,
                    source_domain=urlsplit(normalized_final_url).hostname or "",
                    fetched_at=fetch_result.fetched_at,
                    fetch_provider=fetch_result.provider,
                    http_status=fetch_result.status_code,
                    content_type=fetch_result.content_type[:255],
                    ingestion_status=Document.IngestionStatus.COMPLETED,
                )
                document.chunks.bulk_create(
                    [
                        document.chunks.model(
                            document=document,
                            chunk_text=row["chunk_text"],
                            embedding=row["embedding"],
                        )
                        for row in chunk_rows
                    ]
                )
                return document
        except IntegrityError as exc:
            raise DuplicateURLError() from exc
    except DuplicateURLError:
        raise
    except WebFetchError as exc:
        raise serializers.ValidationError({"url": exc.message}) from exc


def extract_html_content(body: bytes, content_type: str) -> tuple[str, str]:
    from bs4 import BeautifulSoup
    import trafilatura

    html = decode_html(body, content_type)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    for tag in soup(["script", "style", "noscript", "form"]):
        tag.decompose()

    cleaned_html = str(soup)
    extracted = trafilatura.extract(
        cleaned_html,
        include_comments=False,
        include_tables=True,
    )
    text = extracted or soup.get_text("\n", strip=True)
    normalized = normalize_whitespace(text)
    if len(normalized.split()) < 3:
        raise ExtractionError()
    return title, normalized


def decode_html(body: bytes, content_type: str) -> str:
    charset = "utf-8"
    for part in content_type.split(";"):
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value:
            charset = value.strip("\"'")
            break
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def normalize_whitespace(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fallback_title(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.strip("/")
    if path:
        return path.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").strip()[:255]
    return parts.hostname or "Imported webpage"
