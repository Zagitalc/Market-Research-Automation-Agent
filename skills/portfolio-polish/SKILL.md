---
name: portfolio-polish
description: Use when improving README, GitHub presentation, project summary, CV bullet points, screenshots, demo script, architecture explanation, or recruiter-facing explanation.
---

# Portfolio Polish Skill

## Goal

Make the project easy to understand for recruiters, hiring managers, and AI engineering interviewers.

## README should clearly show

- What the project does.
- Why it is relevant to AI engineering.
- Tech stack.
- Architecture diagram or text flow.
- Core features.
- Mock mode vs OpenAI mode.
- LangGraph workflow and reflection retry.
- Evidence retrieval, confidence scoring, and citations.
- File ingestion support and limitations.
- Rate limiting/deployment safety.
- Setup instructions.
- Manual testing steps.
- Screenshots.
- Future roadmap.

When controlled single-page public webpage ingestion is implemented, README and demo materials should also explain:

- URL import form.
- Imported source metadata.
- URL-derived retrieved evidence.
- LangGraph timeline using web-derived evidence.
- Blocked localhost/private-network URL examples.
- robots.txt rejection.
- Weak-evidence behaviour for unrelated questions.

## CV wording style

Use strong engineering language:

- Designed and developed...
- Implemented...
- Integrated...
- Built...
- Added fallback handling...
- Improved reliability...
- Added evidence-tracked RAG workflow...
- Integrated LangGraph orchestration...
- Implemented document ingestion...

After the URL-ingestion milestone is implemented, suitable wording is:

"Implemented controlled public-web ingestion using HTTPX, Beautiful Soup, main-content extraction, robots.txt checks, SSRF protection, and integration with an evidence-backed RAG workflow."

Avoid vague phrases:

- Made an AI app.
- Used AI.
- Built a chatbot.
- Played with LangChain/LangGraph.

Do not claim support for ScrapingBee, Apify, Firecrawl, Zyte, ZenRows, JavaScript rendering, browser automation, multi-page crawling, authenticated scraping, CAPTCHA, or anti-bot bypass until those features are actually implemented.

## Good project positioning

Position this as:

"An internal AI automation platform prototype for market research workflows, using Django, React, RAG-style retrieval, optional OpenAI integration, LangGraph orchestration, document ingestion, evidence citations, and traceable agent steps."

After implementation, URL ingestion can be described as controlled single-page public webpage ingestion.

## Screenshot guidance

Prioritise screenshots that show:

- Main dashboard overview.
- Document knowledge base and upload flow.
- Strong evidence answer.
- Retrieved evidence/citations.
- LangGraph agent timeline.
- Weak-evidence retry with low confidence.
- Delete/clear controls.
- Rate-limit message.

After URL ingestion is implemented, also consider screenshots for:

- URL import form.
- Imported source metadata.
- URL-derived retrieved evidence.
- LangGraph timeline using web-derived evidence.
- Blocked localhost/private-network URL.
- robots.txt rejection.
- Weak-evidence behaviour for an unrelated query.

Avoid screenshots that expose:

- API keys.
- `.env` values.
- private file paths.
- irrelevant terminal clutter.
