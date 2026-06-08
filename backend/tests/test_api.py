import pytest
from rest_framework.test import APIClient

from agents.models import AgentStep
from agents.services import agent_runner
from documents.models import Document, DocumentChunk
from research.models import ResearchRun


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
