---
name: safe-refactor
description: Use when refactoring existing code while preserving current behaviour, API compatibility, tests, and UI behaviour.
---

# Safe Refactor Skill

## Rules

- Do not change public API routes unless explicitly requested.
- Do not remove existing UI features.
- Avoid large rewrites.
- Prefer extracting services/helpers over changing behaviour.
- Keep frontend and backend contracts compatible.
- Update tests when behaviour changes.
- Explain any intentional breaking changes before applying them.

## Checklist

Before editing:
- Identify affected files.
- Identify current behaviour.
- Identify tests or manual checks.

After editing:
- Run relevant tests/checks.
- Summarise changed behaviour.
- Mention any risks.