# AGENTS.md

## Project overview

This is a portfolio project called Market Research Automation Agent.

It is a full-stack Django + React application demonstrating:
- agentic AI workflow structure
- RAG-style document retrieval
- optional OpenAI integration
- mock-first local development
- PostgreSQL-backed storage
- React evidence/timeline UI

## Tech stack

Backend:
- Python
- Django
- Django REST Framework
- PostgreSQL
- OpenAI SDK optional
- JSONField embeddings for current RAG v1

Frontend:
- React
- TypeScript
- Vite

DevOps:
- Docker Compose

## Important rules

- Keep the app runnable without OpenAI API keys.
- Never commit `.env` or real API keys.
- Keep `.env.example` updated when adding environment variables.
- Do not add authentication unless explicitly requested.
- Do not add LangGraph unless explicitly requested.
- Do not migrate to pgvector unless explicitly requested.
- Preserve existing API routes unless the task explicitly requires changing them.
- Prefer small, testable changes over large rewrites.
- After backend changes, run Django checks and backend tests where possible.
- After frontend changes, run frontend tests/build where possible.
- Update README when behaviour, setup, API routes, or manual testing steps change.

## Useful commands

Backend:
```bash
cd backend
.venv/bin/python manage.py check
.venv/bin/pytest
```
