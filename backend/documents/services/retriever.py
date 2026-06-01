from documents.models import DocumentChunk


def retrieve_relevant_chunks(query: str, limit: int = 3) -> list[dict]:
    """Placeholder retrieval until real embeddings and pgvector search are wired in."""
    chunks = DocumentChunk.objects.select_related("document").order_by("-created_at")[:limit]
    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": chunk.document.title,
            "chunk_text": chunk.chunk_text,
            "score": 0.72,
            "query": query,
        }
        for chunk in chunks
    ]
