import pytest
from django.test import override_settings

from agents.models import AgentStep
from agents.services import agent_runner
from research.models import ResearchRun


def _evidence_chunk() -> dict:
    return {
        "chunk_id": 1,
        "document_id": 1,
        "document_title": "Market pulse",
        "chunk_text": "Market research teams are adopting AI automation workflows.",
        "score": 0.91,
        "retrieval_mode": "embedding",
        "ai_mode": "mock",
    }


def _weak_evidence_chunk() -> dict:
    chunk = _evidence_chunk()
    chunk["score"] = 0.2
    return chunk


@pytest.mark.django_db
def test_langgraph_strong_evidence_goes_to_final(monkeypatch):
    calls = []

    def strong_retrieval(query):
        calls.append(query)
        return [_evidence_chunk()]

    monkeypatch.setattr(agent_runner, "retrieve_relevant_chunks", strong_retrieval)
    run = ResearchRun.objects.create(user_query="Analyze AI market research", status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    run.refresh_from_db()
    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    reflection = AgentStep.objects.get(step_type=AgentStep.StepType.REFLECT)
    assert len(calls) == 1
    assert run.status == ResearchRun.Status.COMPLETED
    assert run.confidence_score == 0.78
    assert run.confidence_score == final_step.output_data["confidence_score"]
    assert "Mock answer" in run.final_answer
    assert "[1]" in run.final_answer
    assert final_step.output_data["evidence"][0]["citation_id"] == 1
    assert final_step.output_data["sources_used"] == [
        {
            "citation_id": 1,
            "document_title": "Market pulse",
            "chunk_id": 1,
            "score": 0.91,
            "excerpt": "Market research teams are adopting AI automation workflows.",
        }
    ]
    assert reflection.output_data["enough_evidence"] is True
    assert reflection.output_data["top_score"] == 0.91
    assert reflection.output_data["score_threshold"] == agent_runner.ENOUGH_EVIDENCE_SCORE_THRESHOLD
    assert list(AgentStep.objects.values_list("step_type", flat=True)) == [
        "plan",
        "retrieve",
        "tool_call",
        "reflect",
        "final",
    ]


@pytest.mark.django_db
def test_langgraph_weak_evidence_retries_retrieval_once(monkeypatch):
    calls = []

    def weak_retrieval(query):
        calls.append(query)
        return [_weak_evidence_chunk()]

    monkeypatch.setattr(agent_runner, "retrieve_relevant_chunks", weak_retrieval)
    run = ResearchRun.objects.create(user_query="Analyze a weak market signal", status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    run.refresh_from_db()
    assert len(calls) == 2
    assert calls[0] == run.user_query
    assert calls[1] != run.user_query
    assert calls[1].startswith(run.user_query)
    assert run.status == ResearchRun.Status.COMPLETED
    assert run.confidence_score == 0.35
    assert list(AgentStep.objects.values_list("step_type", flat=True)) == [
        "plan",
        "retrieve",
        "tool_call",
        "reflect",
        "retrieve",
        "tool_call",
        "reflect",
        "final",
    ]
    retrieval_steps = list(AgentStep.objects.filter(step_type=AgentStep.StepType.RETRIEVE))
    assert retrieval_steps[0].input_data["retry_count"] == 0
    assert retrieval_steps[1].input_data["retry_count"] == 1
    assert retrieval_steps[1].input_data["query"] == calls[1]

    reflection_steps = list(AgentStep.objects.filter(step_type=AgentStep.StepType.REFLECT))
    assert all(step.output_data["enough_evidence"] is False for step in reflection_steps)
    assert all(step.output_data["top_score"] == 0.2 for step in reflection_steps)
    assert all(
        step.output_data["score_threshold"] == agent_runner.ENOUGH_EVIDENCE_SCORE_THRESHOLD
        for step in reflection_steps
    )

    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert final_step.output_data["retry_count"] == 1
    assert final_step.output_data["confidence_score"] == 0.35
    assert run.confidence_score == final_step.output_data["confidence_score"]
    assert "current document collection" in run.final_answer.lower()
    assert "does not contain enough relevant evidence" in run.final_answer.lower()
    assert "did not meet the evidence threshold: [1]" in run.final_answer.lower()
    assert final_step.output_data["sources_used"][0]["citation_id"] == 1


@pytest.mark.django_db
def test_no_evidence_answer_references_document_collection_without_echoing_query(monkeypatch):
    monkeypatch.setattr(agent_runner, "retrieve_relevant_chunks", lambda query: [])
    awkward_query = "how many holes we have in Mars"
    run = ResearchRun.objects.create(user_query=awkward_query, status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    run.refresh_from_db()
    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert run.confidence_score == 0.35
    assert final_step.output_data["confidence_score"] == 0.35
    assert run.final_answer == (
        "The current document collection does not contain enough evidence to answer "
        "this question confidently."
    )
    assert awkward_query.lower() not in run.final_answer.lower()
    assert "[1]" not in run.final_answer
    assert final_step.output_data["sources_used"] == []


@pytest.mark.django_db
def test_citation_ids_follow_retrieval_order(monkeypatch):
    second_chunk = {
        **_evidence_chunk(),
        "chunk_id": 2,
        "document_id": 2,
        "document_title": "Buyer survey",
        "chunk_text": "Enterprise buyers want faster automated research workflows.",
        "score": 0.82,
    }
    monkeypatch.setattr(
        agent_runner,
        "retrieve_relevant_chunks",
        lambda query: [_evidence_chunk(), second_chunk],
    )
    run = ResearchRun.objects.create(user_query="Analyze buyer adoption", status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    run.refresh_from_db()
    retrieve_step = AgentStep.objects.get(step_type=AgentStep.StepType.RETRIEVE)
    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert [chunk["citation_id"] for chunk in retrieve_step.output_data["chunks"]] == [1, 2]
    assert "[1]" in run.final_answer
    assert "[2]" in run.final_answer
    assert [source["citation_id"] for source in final_step.output_data["sources_used"]] == [1, 2]
    assert final_step.output_data["sources_used"][1]["document_title"] == "Buyer survey"
    assert final_step.output_data["sources_used"][1]["chunk_id"] == 2


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=True, OPENAI_API_KEY="")
def test_langgraph_mock_mode_works_without_openai_key(monkeypatch):
    monkeypatch.setattr(agent_runner, "retrieve_relevant_chunks", lambda query: [_evidence_chunk()])
    run = ResearchRun.objects.create(user_query="Analyze mock mode", status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert final_step.output_data["ai_mode"] == "mock"
    assert final_step.output_data["model"] is None
    assert final_step.output_data["error"] is None


@pytest.mark.django_db
@override_settings(AI_MOCK_MODE=False, OPENAI_API_KEY="test-key", OPENAI_LLM_MODEL="gpt-4.1-mini")
def test_langgraph_openai_failure_falls_back_and_saves_error(monkeypatch):
    def raise_openai_error(query, chunks):
        raise RuntimeError("OpenAI unavailable")

    monkeypatch.setattr(agent_runner, "retrieve_relevant_chunks", lambda query: [_evidence_chunk()])

    from agents.services import llm_client

    monkeypatch.setattr(llm_client, "_synthesize_with_openai", raise_openai_error)
    run = ResearchRun.objects.create(user_query="Analyze OpenAI fallback", status=ResearchRun.Status.RUNNING)

    agent_runner.run_research_agent(run)

    run.refresh_from_db()
    final_step = AgentStep.objects.get(step_type=AgentStep.StepType.FINAL)
    assert run.status == ResearchRun.Status.COMPLETED
    assert final_step.output_data["ai_mode"] == "mock"
    assert final_step.output_data["model"] == "gpt-4.1-mini"
    assert final_step.output_data["error"]["type"] == "RuntimeError"
    assert final_step.output_data["error"]["fallback"] == "mock_final_answer"
