---
name: safe-refactor
description: Use when refactoring existing code while preserving current behaviour, API compatibility, tests, data safety, and UI behaviour.
---

# Safe Refactor Skill

## Rules

- Do not change public API routes unless explicitly requested.
- Do not remove existing UI features.
- Avoid large rewrites.
- Prefer extracting services/helpers over changing behaviour.
- Keep frontend and backend contracts compatible.
- Preserve mock mode and OpenAI mode.
- Preserve LangGraph routing and weak-evidence retry unless explicitly changing it.
- Preserve document ingestion, delete/clear, and rate limiting behavior.
- Do not expose uploaded source-file URLs unless explicitly requested.
- When URL ingestion is implemented, preserve its security controls and do not bypass destination validation, redirect revalidation, DNS/IP blocking, robots.txt denial handling, throttling, duplicate normalized-URL handling, or failure-without-persistence.
- Do not commit `.env`, secrets, generated media files, or uploaded originals.
- Update tests when behaviour changes.
- Explain any intentional breaking changes before applying them.

## URL-ingestion refactor rules

When refactoring future URL-ingestion code:

- Preserve existing document and research API route compatibility.
- Preserve manual text creation and file upload behavior.
- Validate destinations before outbound requests.
- Revalidate every redirect destination.
- Preserve DNS and blocked-IP validation.
- Preserve robots.txt denial handling.
- Preserve URL-ingestion throttling.
- Preserve duplicate normalized-URL handling.
- Ensure failed ingestion leaves no partial persistent records.
- Preserve mock mode, OpenAI mode, RAG retrieval, citations, confidence scoring, and LangGraph behavior.
- Keep tests for SSRF and private-network blocking, DNS resolution to blocked addresses, redirect validation, robots.txt denial, throttling, duplicate normalized URLs, unsupported content types, failure without persistence, and compatibility of existing document and research endpoints.

## Checklist

Before editing:

- Identify affected files.
- Identify current behaviour.
- Identify public API/response shape impact.
- Identify tests or manual checks.

After editing:

- Run relevant tests/checks.
- Summarise changed behaviour.
- Mention any risks.
- Confirm `.env` and media files are not staged.
