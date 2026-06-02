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
## Current implemented features

The app currently includes:
- Django REST Framework backend
- React + TypeScript frontend
- PostgreSQL storage
- Document creation/list/delete/clear
- Research run creation/list/delete/clear
- Document chunking
- JSONField-backed embeddings
- Mock embedding mode
- Optional OpenAI embedding/final-answer mode
- Evidence retrieval with scores
- AgentStep timeline:
  - plan
  - retrieve
  - tool_call
  - reflect
  - final
- Frontend evidence cards and AI mode badge

## Do not break

When modifying RAG or agent code:
- Keep `AI_MOCK_MODE=true` working without API keys.
- Keep `AI_MOCK_MODE=false` with `OPENAI_API_KEY` working.
- Keep fallback behavior if OpenAI fails.
- Keep delete/clear controls working.
- Keep existing API routes stable.
- Keep frontend evidence/timeline display working.
- Do not commit `.env` or secrets.

## Next major milestone

The next planned AI architecture upgrade is LangGraph integration.

The goal is to replace the custom fixed agent runner with a LangGraph workflow while preserving:
- existing Django API
- existing database models
- existing frontend UI
- existing AgentStep output shape where possible

Expected LangGraph nodes:
1. plan
2. retrieve
3. tool_call
4. reflect
5. final

Expected conditional routing:
- if `enough_evidence=true`, continue to final
- if `enough_evidence=false` and retry count is below limit, retry retrieval once
- if still weak after retry, produce a low-confidence final answer

## Verification

After changes, run where possible:

```bash
cd backend && .venv/bin/python manage.py check
cd backend && .venv/bin/pytest
```
