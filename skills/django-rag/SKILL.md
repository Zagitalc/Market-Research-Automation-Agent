---
name: django-rag
description: Use when modifying Django RAG, retrieval, embeddings, OpenAI/mock mode, document chunking, file ingestion, citations, LangGraph workflow, or research agent behavior in this repository.
---

# Django RAG Skill

## Purpose

Use this skill when working on the Market Research Automation Agent backend, document ingestion, RAG retrieval, embeddings, citations, or LangGraph research workflow.

## Rules

- Preserve mock-first local development.
- Keep `AI_MOCK_MODE=true` working without OpenAI keys.
- Keep `AI_MOCK_MODE=false` working with `OPENAI_API_KEY`.
- If OpenAI calls fail, preserve safe fallback behavior and diagnostic metadata.
- Do not require pgvector unless explicitly requested.
- Keep embeddings in `JSONField` until the pgvector milestone.
- Preserve the LangGraph node flow:
  1. plan
  2. retrieve
  3. tool_call
  4. reflect
  5. final
- Preserve reflection-based retry behavior for weak evidence.
- Preserve low-confidence behavior for weak/no-evidence answers.
- Never commit `.env`, API keys, generated media files, or uploaded originals.

## Key files

- `backend/agents/services/agent_runner.py`
- `backend/agents/services/embedding_provider.py`
- `backend/agents/services/llm_client.py`
- `backend/documents/services/chunker.py`
- `backend/documents/services/retriever.py`
- `backend/documents/services/ingestion.py`
- `backend/documents/serializers.py`
- `backend/documents/views.py`
- `backend/documents/models.py`
- `backend/documents/signals.py`
- `backend/research/models.py`
- `frontend/src/api/client.ts`
- `frontend/src/components/ResearchDashboard.tsx`
- `frontend/src/components/DocumentsPage.tsx`

## Expected retriever output shape

Retriever results should include:

- `chunk_id`
- `document_id`
- `document_title`
- `chunk_text`
- `score`
- `retrieval_mode`
- `citation_id` when citations are enabled

## Expected agent step metadata

Agent steps should include useful metadata where relevant:

- `ai_mode`
- model name if applicable
- retrieved evidence count
- retry count
- evidence threshold
- confidence score
- citation/source metadata
- diagnostic error if fallback occurred

## Current implemented features

The app currently includes:

- Django REST Framework backend
- React + TypeScript frontend
- PostgreSQL storage
- Document creation/list/delete/clear
- Research run creation/list/delete/clear
- TXT, Markdown, and text-based PDF upload ingestion
- Retained original uploaded files in Django media storage
- Automatic document chunking
- JSONField-backed embeddings
- Mock embedding mode
- Optional OpenAI embedding/final-answer mode
- Evidence retrieval with scores
- Citation-aware/evidence-backed final answers
- LangGraph workflow with reflection-based retry
- AgentStep timeline:
  - plan
  - retrieve
  - tool_call
  - reflect
  - final
- Frontend evidence cards and AI mode badge
- API rate limiting for deployment safety

## Do not break

When modifying RAG, ingestion, or agent code:

- Keep `AI_MOCK_MODE=true` working without API keys.
- Keep `AI_MOCK_MODE=false` with `OPENAI_API_KEY` working.
- Keep fallback behavior if OpenAI fails.
- Keep manual document creation working.
- Keep uploaded document ingestion working.
- Keep uploaded source-file cleanup working on delete/clear.
- Keep delete/clear controls working.
- Keep rate limiting behavior working.
- Keep existing API routes stable unless explicitly requested.
- Keep frontend evidence/timeline display working.
- Keep media files ignored by Git.
- Do not commit `.env` or secrets.

## File ingestion rules

The app supports document ingestion through:

- manual pasted text
- uploaded `.txt`
- uploaded `.md`
- uploaded text-based `.pdf`

When modifying ingestion:

- Keep manual document creation working.
- Keep uploaded originals retained in Django media storage.
- Do not expose public source-file download URLs unless explicitly requested.
- Reject failed extraction without creating a persistent `Document` record.
- Keep upload size limit configurable through `DOCUMENT_UPLOAD_MAX_BYTES`.
- Keep PDF support text-based only; do not add OCR unless explicitly requested.
- Keep upload ingestion synchronous until background jobs are explicitly added.
- Ensure uploaded documents still use the existing chunking and embedding pipeline.
- Ensure delete and clear-all remove retained source files.
- Never commit generated media files.

## Verification

After backend changes, run where possible:

```bash
cd backend && .venv/bin/python manage.py check
cd backend && .venv/bin/pytest