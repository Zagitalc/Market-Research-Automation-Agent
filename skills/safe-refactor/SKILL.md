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
- Do not commit `.env`, secrets, generated media files, or uploaded originals.
- Update tests when behaviour changes.
- Explain any intentional breaking changes before applying them.

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