import pytest
from django.test import override_settings

from agents.services.embedding_provider import generate_embedding, get_ai_mode


@pytest.mark.parametrize("text", ["market research", "Market Research"])
@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="")
def test_mock_embeddings_are_deterministic(text):
    first = generate_embedding(text)
    second = generate_embedding(text)

    assert first == second
    assert len(first) == 32
    assert all(isinstance(value, float) for value in first)


@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="test-key")
def test_mock_mode_overrides_openai_key():
    assert get_ai_mode() == "mock"


@override_settings(AI_MOCK_MODE=False, OPENAI_API_KEY="")
def test_missing_key_falls_back_to_mock_mode():
    assert get_ai_mode() == "mock"


@override_settings(AI_MOCK_MODE=False, OPENAI_API_KEY="test-key")
def test_key_and_mock_disabled_enables_openai_mode():
    assert get_ai_mode() == "openai"
