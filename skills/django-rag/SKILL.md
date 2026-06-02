---
name: django-rag
description: Use when modifying the Django RAG, retrieval, embeddings, OpenAI mode, document chunking, or research agent workflow in this repository.
---

# Django RAG Skill

## Purpose

Use this skill when working on the Market Research Automation Agent backend or RAG workflow.

## Rules

- Preserve mock-first local development.
- Keep `AI_MOCK_MODE=true` working without OpenAI keys.
- If adding OpenAI behaviour, keep fallback behaviour when API calls fail.
- Do not require pgvector yet unless explicitly requested.
- Keep embeddings in JSONField until the pgvector milestone.
- Keep research step order stable:
  1. plan
  2. retrieve
  3. tool_call
  4. reflect
  5. final

## Key files

- `backend/agents/services/agent_runner.py`
- `backend/agents/services/embedding_provider.py`
- `backend/agents/services/llm_client.py`
- `backend/documents/services/chunker.py`
- `backend/documents/services/retriever.py`
- `backend/documents/serializers.py`
- `backend/research/models.py`
- `backend/documents/models.py`

## Expected output shape

Retriever results should include:
- `chunk_id`
- `document_id`
- `document_title`
- `chunk_text`
- `score`
- `retrieval_mode`

Agent steps should include useful metadata:
- `ai_mode`
- model name if applicable
- retrieved evidence count
- diagnostic error if fallback occurred

## Verification

After changes, run where possible:

```bash
cd backend && .venv/bin/python manage.py check
cd backend && .venv/bin/pytest
```
