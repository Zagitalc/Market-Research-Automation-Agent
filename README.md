# Market Research Automation Agent

A portfolio-ready full-stack scaffold for an agentic AI market research workflow. The app uses Django REST Framework for the backend, React + TypeScript + Vite for the frontend, PostgreSQL for relational data, and a pgvector-ready database image for future semantic search.

The current agent is intentionally mocked. It records a LangGraph-style sequence of planning, retrieval, tool use, reflection, and final answer steps without calling OpenAI, Anthropic, or any external model API.

## Why This Project Matters

- **Agentic AI:** each research request creates a durable trace of agent steps, making orchestration visible and auditable.
- **RAG foundations:** documents are split into chunks with placeholder embeddings, ready to evolve into pgvector similarity search.
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

## Backend Development

Run tests locally from `backend/` after installing Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

The app uses PostgreSQL during normal runtime. The pytest configuration uses an in-memory SQLite database so API tests can run without a local Postgres service.

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
| POST | `/api/documents/` | Create a document and initial chunk |
| GET | `/api/documents/<id>/` | Retrieve one document |
| GET | `/api/research-runs/` | List research runs |
| POST | `/api/research-runs/` | Create a research run and execute the mock agent |
| GET | `/api/research-runs/<id>/` | Retrieve one research run |
| GET | `/api/research-runs/<id>/steps/` | List agent steps for a run |

## Agent Flow

`POST /api/research-runs/` performs a synchronous mock workflow:

1. Create a `ResearchRun` with status `running`.
2. Generate a mock plan.
3. Retrieve mock relevant `DocumentChunk` records.
4. Create a mock tool call step.
5. Reflect on whether enough evidence exists.
6. Create a final answer.
7. Mark the run `completed`.

The orchestration entry point lives in `backend/agents/services/agent_runner.py`. Retrieval lives in `backend/documents/services/retriever.py`.

## pgvector Readiness

Docker Compose uses `pgvector/pgvector:pg16`. The current `DocumentChunk.embedding` field is a JSON placeholder so the app remains simple for the scaffold. A future migration can enable the `vector` extension and replace the placeholder with a vector column.

## Next Steps

- Add an OpenAI or Anthropic model client.
- Generate real embeddings for document chunks.
- Enable pgvector similarity search with indexed vector columns.
- Add authentication and per-user research runs.
- Add async execution with Celery, Django-Q, or a workflow runner.
- Deploy to Render, Fly.io, or Azure.
