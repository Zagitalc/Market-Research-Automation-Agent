from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from rest_framework import serializers

from documents.models import Document
from documents.services.chunker import create_chunks_for_document


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
