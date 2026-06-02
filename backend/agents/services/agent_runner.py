from agents.models import AgentStep
from agents.services.embedding_provider import get_ai_mode
from agents.services.llm_client import synthesize_final_answer
from documents.services.retriever import retrieve_relevant_chunks
from research.models import ResearchRun


def run_research_agent(research_run: ResearchRun) -> ResearchRun:
    """Synchronous mock agent flow shaped for future LangGraph orchestration."""
    query = research_run.user_query

    plan = [
        "Clarify the market research question",
        "Retrieve relevant source chunks",
        "Check evidence quality",
        "Draft a concise answer with confidence",
    ]
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.PLAN,
        input_data={"query": query, "ai_mode": get_ai_mode()},
        output_data={"plan": plan, "ai_mode": get_ai_mode()},
    )

    chunks = retrieve_relevant_chunks(query)
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.RETRIEVE,
        input_data={"query": query, "limit": 3, "ai_mode": get_ai_mode()},
        output_data={
            "chunks": chunks,
            "retrieved_chunk_count": len(chunks),
            "ai_mode": get_ai_mode(),
        },
    )

    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.TOOL_CALL,
        input_data={"tool": "market_size_estimator", "query": query, "ai_mode": get_ai_mode()},
        output_data={
            "tool": "market_size_estimator",
            "result": "RAG v1 diagnostic tool: retrieved evidence is available for answer synthesis.",
            "evidence_count": len(chunks),
            "ai_mode": get_ai_mode(),
        },
    )

    enough_evidence = len(chunks) > 0
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.REFLECT,
        input_data={"retrieved_chunk_count": len(chunks)},
        output_data={
            "enough_evidence": enough_evidence,
            "notes": "Evidence is sufficient for a portfolio-demo answer." if enough_evidence else "No documents were available.",
            "ai_mode": get_ai_mode(),
        },
    )

    synthesis = synthesize_final_answer(query, chunks)
    final_answer = synthesis["answer"]
    confidence = 0.78 if enough_evidence else 0.42
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.FINAL,
        input_data={"query": query, "chunk_ids": [chunk["chunk_id"] for chunk in chunks], "ai_mode": get_ai_mode()},
        output_data={
            "final_answer": final_answer,
            "confidence_score": confidence,
            "ai_mode": synthesis["ai_mode"],
            "model": synthesis["model"],
            "error": synthesis["error"],
            "evidence": chunks,
        },
    )

    research_run.status = ResearchRun.Status.COMPLETED
    research_run.final_answer = final_answer
    research_run.confidence_score = confidence
    research_run.save(update_fields=["status", "final_answer", "confidence_score", "updated_at"])
    return research_run
