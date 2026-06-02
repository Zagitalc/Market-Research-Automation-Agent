from agents.services.embedding_provider import generate_embedding
from documents.models import Document, DocumentChunk


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 120


def create_chunks_for_document(document: Document) -> list[DocumentChunk]:
    DocumentChunk.objects.filter(document=document).delete()
    chunks = []
    for chunk_text in split_text(document.content):
        chunks.append(
            DocumentChunk.objects.create(
                document=document,
                chunk_text=chunk_text,
                embedding=generate_embedding(chunk_text),
            )
        )
    return chunks


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    clean_text = text.strip()
    if not clean_text:
        return []

    chunks = []
    start = 0
    while start < len(clean_text):
        end = start + chunk_size
        chunks.append(clean_text[start:end].strip())
        if end >= len(clean_text):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]
