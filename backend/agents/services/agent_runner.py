from agents.models import AgentStep
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
        input_data={"query": query},
        output_data={"plan": plan},
    )

    chunks = retrieve_relevant_chunks(query)
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.RETRIEVE,
        input_data={"query": query, "limit": 3},
        output_data={"chunks": chunks},
    )

    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.TOOL_CALL,
        input_data={"tool": "market_size_estimator", "query": query},
        output_data={
            "tool": "market_size_estimator",
            "result": "Mock tool output: market signals found in available sources.",
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
        },
    )

    final_answer = _compose_final_answer(query, chunks, enough_evidence)
    confidence = 0.78 if enough_evidence else 0.42
    AgentStep.objects.create(
        research_run=research_run,
        step_type=AgentStep.StepType.FINAL,
        input_data={"query": query},
        output_data={"final_answer": final_answer, "confidence_score": confidence},
    )

    research_run.status = ResearchRun.Status.COMPLETED
    research_run.final_answer = final_answer
    research_run.confidence_score = confidence
    research_run.save(update_fields=["status", "final_answer", "confidence_score", "updated_at"])
    return research_run


def _compose_final_answer(query: str, chunks: list[dict], enough_evidence: bool) -> str:
    if not enough_evidence:
        return (
            f"Mock answer for '{query}': no source documents are available yet. "
            "Add documents to improve retrieval-grounded analysis."
        )

    source_titles = sorted({chunk["document_title"] for chunk in chunks})
    return (
        f"Mock answer for '{query}': the retrieved evidence suggests a market with clear research signals. "
        f"This draft is grounded in {len(chunks)} chunk(s) from: {', '.join(source_titles)}. "
        "Replace this function with real LLM synthesis when model integration is added."
    )
