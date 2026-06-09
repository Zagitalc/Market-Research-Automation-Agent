from django.conf import settings

from agents.services.embedding_provider import get_ai_mode


def synthesize_final_answer(query: str, chunks: list[dict]) -> dict:
    if get_ai_mode() != "openai":
        return {
            "answer": compose_mock_final_answer(query, chunks),
            "ai_mode": "mock",
            "model": None,
            "error": None,
        }

    try:
        return {
            "answer": _synthesize_with_openai(query, chunks),
            "ai_mode": "openai",
            "model": settings.OPENAI_LLM_MODEL,
            "error": None,
        }
    except Exception as exc:
        return {
            "answer": compose_mock_final_answer(query, chunks),
            "ai_mode": "mock",
            "model": settings.OPENAI_LLM_MODEL,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "fallback": "mock_final_answer",
            },
        }


def compose_mock_final_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return (
            f"Mock answer for '{query}': no source documents are available yet. "
            "Add documents to improve retrieval-grounded analysis."
        )

    evidence_summary = "; ".join(
        f"[{chunk.get('citation_id', index)}] {chunk['document_title']}: {chunk['chunk_text'][:140]}"
        for index, chunk in enumerate(chunks[:3], start=1)
    )
    return (
        f"Mock answer for '{query}': the retrieved sources suggest relevant market signals. "
        f"Evidence used: {evidence_summary}"
    )


def _synthesize_with_openai(query: str, chunks: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    evidence = "\n\n".join(
        (
            f"[{chunk.get('citation_id', index)}] Source: {chunk['document_title']}\n"
            f"Score: {chunk['score']}\nText: {chunk['chunk_text']}"
        )
        for index, chunk in enumerate(chunks, start=1)
    )
    prompt = (
        "Answer the market research question using only the evidence below. "
        "Be concise, cite factual claims with the supplied numeric markers such as [1], "
        "and mention uncertainty if evidence is thin. Do not invent citation markers.\n\n"
        f"Question: {query}\n\nEvidence:\n{evidence or 'No evidence was retrieved.'}"
    )
    response = client.responses.create(
        model=settings.OPENAI_LLM_MODEL,
        input=prompt,
    )
    return response.output_text
