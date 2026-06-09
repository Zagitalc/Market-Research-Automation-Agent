# AGENTS.md

## Project overview

This is a portfolio project called Market Research Automation Agent.

It is a full-stack Django + React application demonstrating:
- agentic AI workflow structure
- LangGraph orchestration with reflection-based retry
- RAG-style document retrieval
- optional OpenAI integration
- mock-first local development
- PostgreSQL-backed storage
- JSONField embeddings for current RAG v1
- React evidence/timeline UI
- document ingestion for TXT, Markdown, and text-based PDF uploads
- deployment-safety rate limiting

## Tech stack

Backend:
- Python
- Django
- Django REST Framework
- PostgreSQL
- OpenAI SDK optional
- LangGraph
- JSONField embeddings for current RAG v1
- pypdf for text-based PDF extraction

Frontend:
- React
- TypeScript
- Vite

DevOps:
- Docker Compose

## Important rules

- Keep the app runnable without OpenAI API keys.
- Never commit `.env` or real API keys.
- Never commit generated media files or uploaded originals.
- Keep `.env.example` updated when adding environment variables.
- Keep media/upload directories ignored by Git.
- Do not add authentication unless explicitly requested.
- Do not change LangGraph workflow/routing unless explicitly requested.
- Do not migrate to pgvector unless explicitly requested.
- Do not add OCR, URL ingestion, or background jobs unless explicitly requested.
- Do not expose uploaded source-file download URLs unless explicitly requested.
- Preserve existing API routes unless the task explicitly requires changing them.
- Preserve mock mode, OpenAI mode, RAG retrieval, LangGraph retry, delete/clear controls, file ingestion, and rate limiting unless explicitly requested.
- Prefer small, testable changes over large rewrites.
- After backend changes, run Django checks and backend tests where possible.
- After frontend changes, run frontend tests/build where possible.
- Update README when behaviour, setup, API routes, screenshots, environment variables, or manual testing steps change.

## Useful commands

Backend:

```bash
cd backend
.venv/bin/python manage.py check
.venv/bin/pytest