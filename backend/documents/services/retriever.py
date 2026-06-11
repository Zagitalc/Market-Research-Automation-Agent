import math
import re

from agents.services.embedding_provider import generate_embedding, get_ai_mode
from documents.models import DocumentChunk


MOCK_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "do",
    "does",
    "for",
    "have",
    "how",
    "in",
    "is",
    "many",
    "of",
    "on",
    "the",
    "to",
    "we",
    "what",
    "which",
    "who",
}


def retrieve_relevant_chunks(query: str, limit: int = 3) -> list[dict]:
    chunks = list(DocumentChunk.objects.select_related("document").all())
    if not chunks:
        return []

    ai_mode = get_ai_mode()
    query_embedding = generate_embedding(query) if ai_mode == "openai" else []
    scored_chunks = []
    for chunk in chunks:
        if ai_mode == "mock":
            score = mock_lexical_score(query, chunk.chunk_text)
            retrieval_mode = "keyword"
        elif _has_embedding(chunk.embedding) and query_embedding:
            score = cosine_similarity(query_embedding, chunk.embedding)
            retrieval_mode = "embedding"
        else:
            score = keyword_score(query, chunk.chunk_text)
            retrieval_mode = "keyword"
        scored_chunks.append(_format_chunk(chunk, score, retrieval_mode, ai_mode))

    scored_chunks.sort(key=lambda result: (result["score"], result["chunk_id"]), reverse=True)
    return scored_chunks[:limit]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right))
    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))
    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0
    return round(dot_product / (left_magnitude * right_magnitude), 6)


def keyword_score(query: str, text: str) -> float:
    query_terms = set(_tokenize(query))
    if not query_terms:
        return 0.0
    text_terms = set(_tokenize(text))
    if not text_terms:
        return 0.0
    return round(len(query_terms & text_terms) / len(query_terms), 6)


def mock_lexical_score(query: str, text: str) -> float:
    query_terms = set(_mock_terms(query))
    if not query_terms:
        return 0.0
    text_terms = set(_mock_terms(text))
    if not text_terms:
        return 0.0
    return round(len(query_terms & text_terms) / len(query_terms), 6)


def _format_chunk(chunk: DocumentChunk, score: float, retrieval_mode: str, ai_mode: str) -> dict:
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "document_title": chunk.document.title,
        "chunk_text": chunk.chunk_text,
        "score": score,
        "retrieval_mode": retrieval_mode,
        "ai_mode": ai_mode,
    }


def _has_embedding(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(isinstance(item, (int, float)) for item in value)


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _mock_terms(value: str) -> list[str]:
    return [_mock_stem(term) for term in _tokenize(value) if term not in MOCK_STOP_WORDS]


def _mock_stem(term: str) -> str:
    for suffix in ("ing", "ed"):
        if term.endswith(suffix) and len(term) > len(suffix) + 3:
            return term[: -len(suffix)]
    return term
