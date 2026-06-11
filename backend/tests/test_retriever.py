import pytest
from django.test import override_settings

from documents.models import Document, DocumentChunk
from documents.services import retriever
from documents.services.retriever import (
    cosine_similarity,
    keyword_score,
    mock_lexical_score,
    retrieve_relevant_chunks,
)


def test_cosine_similarity_with_known_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [1.0, 1.0]) == 1.0


def test_keyword_score_counts_query_overlap():
    assert keyword_score("ai automation market", "AI automation budgets are growing") == pytest.approx(2 / 3)


def test_mock_lexical_score_normalizes_common_words_and_adoption_terms():
    query = "Which teams are adopting AI research tools fastest?"
    text = (
        "AI research tools are being adopted fastest by marketing, retail, customer insight, "
        "and sales enablement teams."
    )

    assert mock_lexical_score(query, text) == 1.0


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="")
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


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="")
def test_mock_retrieval_scores_relevant_uploaded_evidence_above_threshold():
    text = (
        "AI research tools are being adopted fastest by marketing, retail, customer insight, "
        "and sales enablement teams."
    )
    document = Document.objects.create(title="AI research tools", source_type="upload", content=text)
    DocumentChunk.objects.create(document=document, chunk_text=text, embedding=[-1.0, 0.0])

    result = retrieve_relevant_chunks("Which teams are adopting AI research tools fastest?")[0]

    assert result["retrieval_mode"] == "keyword"
    assert result["ai_mode"] == "mock"
    assert result["score"] >= 0.5


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="")
def test_mock_retrieval_keeps_unrelated_query_below_threshold():
    text = "AI research tools are adopted by marketing and customer insight teams."
    document = Document.objects.create(title="AI research tools", source_type="upload", content=text)
    DocumentChunk.objects.create(document=document, chunk_text=text, embedding=[1.0, 0.0])

    result = retrieve_relevant_chunks("How many holes do we have in Mars?")[0]

    assert result["score"] < 0.5


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=False, OPENAI_API_KEY="test-key")
def test_openai_mode_still_uses_embedding_similarity(monkeypatch):
    document = Document.objects.create(title="Vector source", source_type="note", content="Vector evidence")
    DocumentChunk.objects.create(
        document=document,
        chunk_text="Vector evidence",
        embedding=[1.0, 0.0],
    )
    monkeypatch.setattr(retriever, "generate_embedding", lambda query: [1.0, 0.0])

    result = retrieve_relevant_chunks("Unrelated lexical terms")[0]

    assert result["retrieval_mode"] == "embedding"
    assert result["ai_mode"] == "openai"
    assert result["score"] == 1.0
