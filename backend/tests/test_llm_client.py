from django.test import override_settings

from agents.services import llm_client


@override_settings(AI_MOCK_MODE=False, OPENAI_API_KEY="test-key", OPENAI_LLM_MODEL="gpt-4.1-mini")
def test_openai_failure_falls_back_to_mock_answer(monkeypatch):
    def raise_openai_error(query, chunks):
        raise RuntimeError("OpenAI unavailable")

    monkeypatch.setattr(llm_client, "_synthesize_with_openai", raise_openai_error)

    result = llm_client.synthesize_final_answer(
        "Analyze automation",
        [{"document_title": "Market pulse", "chunk_text": "AI automation budgets are growing.", "score": 0.9}],
    )

    assert result["ai_mode"] == "mock"
    assert result["model"] == "gpt-4.1-mini"
    assert result["error"]["type"] == "RuntimeError"
    assert result["error"]["fallback"] == "mock_final_answer"
    assert "Mock answer" in result["answer"]
