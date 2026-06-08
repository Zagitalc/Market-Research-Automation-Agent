# Market Research Automation Agent

A portfolio-ready full-stack scaffold for an agentic AI market research workflow. The app uses Django REST Framework for the backend, React + TypeScript + Vite for the frontend, PostgreSQL for relational data, and a pgvector-ready database image for future semantic search.

The current app is RAG v1: documents are chunked, chunks receive embeddings, retrieval returns evidence with scores, and research runs save a visible agent trace. OpenAI integration is optional; mock mode remains the default so the app runs without API keys.

## Why This Project Matters

- **Agentic AI:** each research request creates a durable trace of agent steps, making orchestration visible and auditable.
- **LangGraph orchestration:** the research workflow runs through a typed graph with explicit planning, retrieval, tool, reflection, retry, and final-answer nodes.
- **RAG foundations:** documents are split into chunks, embeddings are stored, and retrieved evidence is shown in the UI.
- **Django and SQL:** the backend uses Django models, migrations, DRF serializers, viewsets, and PostgreSQL.
- **React:** the frontend provides a dashboard for query submission, run inspection, agent timelines, and source document management.
- **DevOps:** Docker Compose runs PostgreSQL, Django, and Vite together for local development.

## Project Structure

```text
backend/
  config/                 Django project settings and URLs
  accounts/               Placeholder app for future auth
  documents/              Document and chunk models, API, retrieval service
  research/               ResearchRun model and API
  agents/                 AgentStep model and LangGraph research workflow
frontend/
  src/                    React TypeScript app
docker-compose.yml
.env.example
README.md
```

## Local Setup

1. Copy environment defaults:

   ```bash
   cp .env.example .env
   ```

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Open the app:

   - Frontend: <http://localhost:5173>
   - Backend API: <http://localhost:8000/api/>
   - Health check: <http://localhost:8000/api/health/>

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `AI_MOCK_MODE` | `true` | When `true`, always use deterministic mock embeddings and mock final answers. |
| `OPENAI_API_KEY` | empty | Enables OpenAI mode only when `AI_MOCK_MODE=false`. |
| `OPENAI_LLM_MODEL` | `gpt-4.1-mini` | Model used for final-answer synthesis in OpenAI mode. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model used for chunk/query embeddings in OpenAI mode. |
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Frontend API base URL. |

Mock mode behavior:

```env
AI_MOCK_MODE=true
OPENAI_API_KEY=
```

OpenAI mode behavior:

```env
AI_MOCK_MODE=false
OPENAI_API_KEY=your-real-key
OPENAI_LLM_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

If `AI_MOCK_MODE=false` but no key is present, the backend falls back to mock mode. If an OpenAI final-answer call fails, the app saves diagnostic metadata in the final agent step and falls back to a mock answer.

## Backend Development

Run tests locally from `backend/` after installing Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

The app uses PostgreSQL during normal runtime. The pytest configuration uses an in-memory SQLite database so API tests can run without a local Postgres service.

Backfill embeddings for existing chunks that still have empty embeddings:

```bash
python manage.py backfill_chunk_embeddings --dry-run
python manage.py backfill_chunk_embeddings
```

## Frontend Development

Run tests locally from `frontend/` after installing Node dependencies:

```bash
npm install
npm test
```

Start Vite without Docker:

```bash
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health/` | Service health check |
| GET | `/api/documents/` | List documents |
| POST | `/api/documents/` | Create a document, chunks, and chunk embeddings |
| GET | `/api/documents/<id>/` | Retrieve one document |
| DELETE | `/api/documents/<id>/` | Delete one document and cascade-delete its chunks |
| DELETE | `/api/documents/clear/` | Delete all documents and chunks |
| GET | `/api/research-runs/` | List research runs |
| POST | `/api/research-runs/` | Create a research run and execute the RAG v1 agent |
| GET | `/api/research-runs/<id>/` | Retrieve one research run |
| DELETE | `/api/research-runs/<id>/` | Delete one research run and cascade-delete its agent steps |
| DELETE | `/api/research-runs/clear/` | Delete all research runs and agent steps |
| GET | `/api/research-runs/<id>/steps/` | List agent steps for a run |

Clear-all responses include `deleted` for top-level records, `deleted_rows` for all database rows including cascades, and `details` for Django's per-model delete breakdown.

## LangGraph Agent Flow

`POST /api/research-runs/` performs a synchronous RAG v1 workflow through LangGraph while keeping the Django API response shape stable:

1. Create a `ResearchRun` with status `running`.
2. Start a typed LangGraph state with the query, AI mode, retry count, retrieved chunks, reflection data, final answer fields, and errors.
3. Run the graph nodes in order: `plan`, `retrieve`, `tool_call`, `reflect`, and `final`.
4. After `reflect`, route conditionally:
   - a top retrieval score of at least `0.5` is enough evidence and goes directly to `final`
   - a score below `0.5` retries `retrieve` once with a refined query
   - weak evidence after one retry goes to `final` with `0.35` confidence and an explicit insufficiency notice
5. Save each node as an `AgentStep` record using the existing step types.
6. Create a final answer with OpenAI when enabled, otherwise mock synthesis.
7. Mark the run `completed`.

The orchestration entry point and graph definition live in `backend/agents/services/agent_runner.py`. Retrieval lives in `backend/documents/services/retriever.py`. Final answer synthesis remains in `backend/agents/services/llm_client.py`, so OpenAI failures still fall back to mock answers with diagnostic metadata saved in the final step.

## Manual Test Flow

1. Open <http://localhost:5173>.
2. Go to **Documents** and add a document with market research content.
3. Go to **Research** and submit a query related to that document.
4. Confirm the run detail shows:
   - final answer
   - Mock mode or OpenAI mode badge
   - retrieved evidence
   - document title
   - retrieval score
   - full agent step timeline
5. Delete one document and confirm it disappears from the Documents list.
6. Add multiple documents, click **Clear all**, confirm the prompt, and verify the empty state.
7. Delete one research run and confirm the run list/detail selection updates.
8. Add multiple research runs, click **Clear history**, confirm the prompt, and verify no history remains.

## pgvector Readiness

Docker Compose uses `pgvector/pgvector:pg16`. The current `DocumentChunk.embedding` field remains a JSONField for RAG v1. A future migration can enable the `vector` extension and replace the JSON placeholder with a vector column.

## Next Steps

- Enable pgvector similarity search with indexed vector columns.
- Add richer chunking and source citations.
- Add authentication and per-user research runs.
- Add LangGraph checkpointing or streaming when the workflow needs resumable or live-running agent traces.
- Add async execution with Celery, Django-Q, or a workflow runner.
- Deploy to Render, Fly.io, or Azure.
