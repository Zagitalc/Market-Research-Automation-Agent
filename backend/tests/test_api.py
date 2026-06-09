import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from agents.models import AgentStep
from agents.services import agent_runner
from documents.models import Document, DocumentChunk
from research.models import ResearchRun


THROTTLED_API_SETTINGS = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",
        "research_run_create": "1/min",
        "document_create": "1/min",
    },
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_health_endpoint(api_client):
    response = api_client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_document_create_list_and_detail(api_client):
    payload = {
        "title": "AI procurement report",
        "source_type": "report",
        "content": "Enterprise buyers are increasing AI automation budgets.",
    }

    create_response = api_client.post("/api/documents/", payload, format="json")
    assert create_response.status_code == 201
    document_id = create_response.json()["id"]

    list_response = api_client.get("/api/documents/")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == payload["title"]

    detail_response = api_client.get(f"/api/documents/{document_id}/")
    assert detail_response.status_code == 200
    assert detail_response.json()["chunks"][0]["chunk_text"] == payload["content"]
    assert detail_response.json()["chunks"][0]["embedding"]


@pytest.mark.django_db
def test_delete_document_removes_document_and_chunks(api_client):
    document = Document.objects.create(title="Delete me", source_type="note", content="Old source")
    DocumentChunk.objects.create(document=document, chunk_text="Old source", embedding=[1.0])

    response = api_client.delete(f"/api/documents/{document.id}/")

    assert response.status_code == 204
    assert Document.objects.count() == 0
    assert DocumentChunk.objects.count() == 0


@pytest.mark.django_db
def test_clear_documents_returns_counts_and_cascades_chunks(api_client):
    first = Document.objects.create(title="First", source_type="note", content="First source")
    second = Document.objects.create(title="Second", source_type="note", content="Second source")
    DocumentChunk.objects.create(document=first, chunk_text="First source", embedding=[1.0])
    DocumentChunk.objects.create(document=second, chunk_text="Second source", embedding=[1.0])

    response = api_client.delete("/api/documents/clear/")

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 2
    assert body["deleted_rows"] == 4
    assert body["details"]["documents.Document"] == 2
    assert body["details"]["documents.DocumentChunk"] == 2
    assert Document.objects.count() == 0
    assert DocumentChunk.objects.count() == 0


@pytest.mark.django_db
def test_research_run_creation_completes_mock_agent_flow(api_client, monkeypatch):
    document = Document.objects.create(
        title="Market pulse",
        source_type="note",
        content="Automation platforms are moving from dashboards to agentic workflows.",
    )
    chunk = DocumentChunk.objects.create(document=document, chunk_text=document.content, embedding=[1.0, 0.0])
    monkeypatch.setattr(
        agent_runner,
        "retrieve_relevant_chunks",
        lambda query: [
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_title": document.title,
                "chunk_text": chunk.chunk_text,
                "score": 0.9,
                "retrieval_mode": "embedding",
                "ai_mode": "mock",
            }
        ],
    )

    response = api_client.post(
        "/api/research-runs/",
        {"user_query": "What is happening in market research automation?"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == ResearchRun.Status.COMPLETED
    assert body["confidence_score"] == 0.78
    assert "Mock answer" in body["final_answer"]

    step_types = list(AgentStep.objects.values_list("step_type", flat=True))
    assert step_types == ["plan", "retrieve", "tool_call", "reflect", "final"]

    retrieve_step = AgentStep.objects.get(step_type=AgentStep.StepType.RETRIEVE)
    assert retrieve_step.output_data["chunks"][0]["document_title"] == "Market pulse"
    assert retrieve_step.output_data["chunks"][0]["retrieval_mode"] == "embedding"

    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert final_step.output_data["ai_mode"] == "mock"
    assert final_step.output_data["evidence"]


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLED_API_SETTINGS)
def test_research_run_creation_is_throttled_with_clear_429(api_client, monkeypatch):
    cache.clear()
    agent_calls = []

    def complete_research_run(research_run):
        agent_calls.append(research_run.id)
        research_run.status = ResearchRun.Status.COMPLETED
        research_run.final_answer = "Test answer"
        research_run.confidence_score = 0.78
        research_run.save()
        return research_run

    monkeypatch.setattr("research.views.run_research_agent", complete_research_run)

    first_response = api_client.post(
        "/api/research-runs/",
        {"user_query": "First request"},
        format="json",
    )
    throttled_response = api_client.post(
        "/api/research-runs/",
        {"user_query": "Second request"},
        format="json",
    )

    assert first_response.status_code == 201
    assert throttled_response.status_code == 429
    assert throttled_response.json()["code"] == "rate_limited"
    assert "Rate limit exceeded" in throttled_response.json()["detail"]
    assert throttled_response.json()["retry_after"] > 0
    assert len(agent_calls) == 1


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLED_API_SETTINGS)
def test_document_creation_is_throttled(api_client):
    cache.clear()
    first_response = api_client.post(
        "/api/documents/",
        {"title": "First", "source_type": "note", "content": "First document"},
        format="json",
    )
    throttled_response = api_client.post(
        "/api/documents/",
        {"title": "Second", "source_type": "note", "content": "Second document"},
        format="json",
    )

    assert first_response.status_code == 201
    assert throttled_response.status_code == 429
    assert throttled_response.json()["code"] == "rate_limited"
    assert Document.objects.count() == 1


@pytest.mark.django_db
def test_research_run_steps_endpoint(api_client):
    run = ResearchRun.objects.create(user_query="Analyze fintech adoption", status=ResearchRun.Status.RUNNING)
    AgentStep.objects.create(
        research_run=run,
        step_type=AgentStep.StepType.PLAN,
        input_data={"query": run.user_query},
        output_data={"plan": ["retrieve"]},
    )

    response = api_client.get(f"/api/research-runs/{run.id}/steps/")

    assert response.status_code == 200
    assert response.json()[0]["step_type"] == "plan"


@pytest.mark.django_db
def test_delete_research_run_removes_run_and_agent_steps(api_client):
    run = ResearchRun.objects.create(user_query="Delete this run", status=ResearchRun.Status.COMPLETED)
    AgentStep.objects.create(
        research_run=run,
        step_type=AgentStep.StepType.PLAN,
        input_data={},
        output_data={},
    )

    response = api_client.delete(f"/api/research-runs/{run.id}/")

    assert response.status_code == 204
    assert ResearchRun.objects.count() == 0
    assert AgentStep.objects.count() == 0


@pytest.mark.django_db
def test_clear_research_runs_returns_counts_and_cascades_steps(api_client):
    first = ResearchRun.objects.create(user_query="First", status=ResearchRun.Status.COMPLETED)
    second = ResearchRun.objects.create(user_query="Second", status=ResearchRun.Status.COMPLETED)
    AgentStep.objects.create(research_run=first, step_type=AgentStep.StepType.PLAN, input_data={}, output_data={})
    AgentStep.objects.create(research_run=second, step_type=AgentStep.StepType.PLAN, input_data={}, output_data={})

    response = api_client.delete("/api/research-runs/clear/")

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 2
    assert body["deleted_rows"] == 4
    assert body["details"]["research.ResearchRun"] == 2
    assert body["details"]["agents.AgentStep"] == 2
    assert ResearchRun.objects.count() == 0
    assert AgentStep.objects.count() == 0
