import pytest

from documents.models import Document, DocumentChunk
from documents.services.retriever import cosine_similarity, keyword_score, retrieve_relevant_chunks


def test_cosine_similarity_with_known_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [1.0, 1.0]) == 1.0


def test_keyword_score_counts_query_overlap():
    assert keyword_score("ai automation market", "AI automation budgets are growing") == pytest.approx(2 / 3)


@pytest.mark.django_db
def test_retrieval_falls_back_to_keyword_when_embeddings_missing():
    document = Document.objects.create(title="Survey", source_type="note", content="AI automation budgets")
    DocumentChunk.objects.create(document=document, chunk_text="AI automation budgets", embedding=[])

    results = retrieve_relevant_chunks("automation budgets")

    assert results[0]["retrieval_mode"] == "keyword"
    assert results[0]["document_title"] == "Survey"
    assert set(results[0]) == {
        "chunk_id",
        "document_id",
        "document_title",
        "chunk_text",
        "score",
        "retrieval_mode",
        "ai_mode",
    }
