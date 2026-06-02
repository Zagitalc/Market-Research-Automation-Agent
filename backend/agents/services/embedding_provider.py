import hashlib
import math

from django.conf import settings


MOCK_EMBEDDING_DIMENSIONS = 32


def get_ai_mode() -> str:
    if settings.AI_MOCK_MODE or not settings.OPENAI_API_KEY:
        return "mock"
    return "openai"


def generate_embedding(text: str) -> list[float]:
    if get_ai_mode() == "openai":
        return _generate_openai_embedding(text)
    return generate_mock_embedding(text)


def generate_mock_embedding(text: str) -> list[float]:
    normalized = text.strip().lower().encode("utf-8")
    seed = hashlib.sha256(normalized).digest()
    values: list[float] = []

    while len(values) < MOCK_EMBEDDING_DIMENSIONS:
        seed = hashlib.sha256(seed).digest()
        values.extend(((byte / 127.5) - 1.0) for byte in seed)

    vector = values[:MOCK_EMBEDDING_DIMENSIONS]
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / magnitude, 6) for value in vector]


def _generate_openai_embedding(text: str) -> list[float]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    return list(response.data[0].embedding)
