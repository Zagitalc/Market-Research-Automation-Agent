# Market Research Automation Agent

A portfolio-ready full-stack scaffold for an agentic AI market research workflow. The app uses Django REST Framework for the backend, React + TypeScript + Vite for the frontend, PostgreSQL for relational data, and a pgvector-ready database image for future semantic search.

The current app is RAG v1: documents are chunked, chunks receive embeddings, retrieval returns evidence with scores, and research runs save a visible agent trace. OpenAI integration is optional; mock mode remains the default so the app runs without API keys.

## Why This Project Matters

- **Agentic AI:** each research request creates a durable trace of agent steps, making orchestration visible and auditable.
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
  agents/                 AgentStep model and mock agent runner
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
| GET | `/api/research-runs/` | List research runs |
| POST | `/api/research-runs/` | Create a research run and execute the RAG v1 agent |
| GET | `/api/research-runs/<id>/` | Retrieve one research run |
| GET | `/api/research-runs/<id>/steps/` | List agent steps for a run |

## Agent Flow

`POST /api/research-runs/` performs a synchronous RAG v1 workflow:

1. Create a `ResearchRun` with status `running`.
2. Generate a deterministic plan step.
3. Retrieve relevant `DocumentChunk` records using embedding similarity or keyword fallback.
4. Create a diagnostic tool call step.
5. Reflect on whether enough evidence exists.
6. Create a final answer with OpenAI when enabled, otherwise mock synthesis.
7. Mark the run `completed`.

The orchestration entry point lives in `backend/agents/services/agent_runner.py`. Retrieval lives in `backend/documents/services/retriever.py`.

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

## pgvector Readiness

Docker Compose uses `pgvector/pgvector:pg16`. The current `DocumentChunk.embedding` field remains a JSONField for RAG v1. A future migration can enable the `vector` extension and replace the JSON placeholder with a vector column.

## Next Steps

- Enable pgvector similarity search with indexed vector columns.
- Add richer chunking and source citations.
- Add authentication and per-user research runs.
- Add LangGraph or another workflow engine when orchestration needs branching/streaming.
- Add async execution with Celery, Django-Q, or a workflow runner.
- Deploy to Render, Fly.io, or Azure.
