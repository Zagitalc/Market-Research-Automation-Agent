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
- upcoming controlled single-page public webpage ingestion through direct HTTP/HTTPS fetching and readable HTML extraction
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

Proposed dependencies for the upcoming URL-ingestion milestone:
- httpx
- beautifulsoup4
- trafilatura

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
- Do not add OCR, URL ingestion, or background jobs unless explicitly requested; controlled single-page URL ingestion is permitted only for the explicitly requested URL-ingestion milestone.
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
```

## Upcoming URL-ingestion rules

When controlled URL ingestion is implemented, keep it limited to individual public HTTP/HTTPS webpages and feed extracted text into the existing document, chunking, embedding, retrieval, citation, and LangGraph workflow.

- Do not add JavaScript rendering, Playwright, Selenium, multi-page crawling, link following, authenticated/login-page scraping, CAPTCHA or anti-bot bypass, proxy rotation, hosted scraping-provider integration, scheduled scraping, background jobs, OCR, or pgvector migration unless explicitly requested.
- Do not store cookies, authorization headers, credentials, hosted-provider keys, or unnecessary raw response headers.
- Preserve SSRF protection, destination validation before requests, DNS/IP validation, redirect revalidation, robots.txt checks, request limits, throttling, and failure without partial persistence.
- Preserve manual text ingestion, file ingestion, RAG retrieval, citations, OpenAI/mock modes, LangGraph workflow, delete/clear behaviour, existing rate limits, and API compatibility.
