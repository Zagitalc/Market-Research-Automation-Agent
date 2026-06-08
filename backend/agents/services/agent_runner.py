from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.models import AgentStep
from agents.services.embedding_provider import get_ai_mode
from agents.services.llm_client import synthesize_final_answer
from documents.services.retriever import retrieve_relevant_chunks
from research.models import ResearchRun


ENOUGH_EVIDENCE_SCORE_THRESHOLD = 0.5
STRONG_EVIDENCE_CONFIDENCE = 0.78
WEAK_EVIDENCE_CONFIDENCE = 0.35


class ResearchAgentState(TypedDict):
    research_run_id: int
    user_query: str
    plan: list[str]
    retrieved_chunks: list[dict[str, Any]]
    tool_output: dict[str, Any]
    reflection: dict[str, Any]
    final_answer: str
    confidence_score: float
    ai_mode: str
    retry_count: int
    retrieval_query: str
    errors: list[dict[str, Any]]


def run_research_agent(research_run: ResearchRun) -> ResearchRun:
    """Run the research workflow through LangGraph while preserving the API contract."""
    graph = build_research_graph()
    final_state = graph.invoke(
        {
            "research_run_id": research_run.id,
            "user_query": research_run.user_query,
            "plan": [],
            "retrieved_chunks": [],
            "tool_output": {},
            "reflection": {},
            "final_answer": "",
            "confidence_score": 0.0,
            "ai_mode": get_ai_mode(),
            "retry_count": 0,
            "retrieval_query": research_run.user_query,
            "errors": [],
        }
    )

    research_run.status = ResearchRun.Status.COMPLETED
    research_run.final_answer = final_state["final_answer"]
    research_run.confidence_score = final_state["confidence_score"]
    research_run.save(update_fields=["status", "final_answer", "confidence_score", "updated_at"])
    return research_run


def build_research_graph():
    graph = StateGraph(ResearchAgentState)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("tool_call", tool_call_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("final", final_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "tool_call")
    graph.add_edge("tool_call", "reflect")
    graph.add_conditional_edges(
        "reflect",
        route_after_reflection,
        {
            "retry": "retrieve",
            "final": "final",
        },
    )
    graph.add_edge("final", END)
    return graph.compile()


def plan_node(state: ResearchAgentState) -> dict[str, Any]:
    plan = [
        "Clarify the market research question",
        "Retrieve relevant source chunks",
        "Check evidence quality",
        "Draft a concise answer with confidence",
    ]
    _create_step(
        state,
        AgentStep.StepType.PLAN,
        input_data={"query": state["user_query"], "ai_mode": state["ai_mode"]},
        output_data={"plan": plan, "ai_mode": state["ai_mode"]},
    )
    return {"plan": plan, "ai_mode": get_ai_mode()}


def retrieve_node(state: ResearchAgentState) -> dict[str, Any]:
    retry_count = state["retry_count"]
    if _is_retry_retrieval(state):
        retry_count += 1

    retrieval_query = state.get("retrieval_query") or state["user_query"]
    chunks = retrieve_relevant_chunks(retrieval_query)
    _create_step(
        state,
        AgentStep.StepType.RETRIEVE,
        input_data={
            "query": retrieval_query,
            "original_query": state["user_query"],
            "limit": 3,
            "ai_mode": get_ai_mode(),
            "retry_count": retry_count,
        },
        output_data={
            "chunks": chunks,
            "retrieved_chunk_count": len(chunks),
            "ai_mode": get_ai_mode(),
            "retry_count": retry_count,
        },
    )
    return {
        "retrieved_chunks": chunks,
        "ai_mode": get_ai_mode(),
        "retry_count": retry_count,
    }


def tool_call_node(state: ResearchAgentState) -> dict[str, Any]:
    tool_output = {
        "tool": "market_size_estimator",
        "result": "RAG v1 diagnostic tool: retrieved evidence is available for answer synthesis.",
        "evidence_count": len(state["retrieved_chunks"]),
        "ai_mode": get_ai_mode(),
        "retry_count": state["retry_count"],
    }
    _create_step(
        state,
        AgentStep.StepType.TOOL_CALL,
        input_data={
            "tool": "market_size_estimator",
            "query": state["user_query"],
            "ai_mode": get_ai_mode(),
            "retry_count": state["retry_count"],
        },
        output_data=tool_output,
    )
    return {"tool_output": tool_output, "ai_mode": get_ai_mode()}


def reflect_node(state: ResearchAgentState) -> dict[str, Any]:
    top_score = _top_retrieval_score(state["retrieved_chunks"])
    enough_evidence = top_score >= ENOUGH_EVIDENCE_SCORE_THRESHOLD
    retrieval_query = state["retrieval_query"]
    if not enough_evidence and state["retry_count"] < 1:
        retrieval_query = _build_retry_query(state["user_query"])

    reflection = {
        "enough_evidence": enough_evidence,
        "top_score": top_score,
        "score_threshold": ENOUGH_EVIDENCE_SCORE_THRESHOLD,
        "notes": (
            "The top retrieval score meets the evidence threshold."
            if enough_evidence
            else "Available evidence is below the required score threshold."
        ),
        "ai_mode": get_ai_mode(),
        "retry_count": state["retry_count"],
    }
    _create_step(
        state,
        AgentStep.StepType.REFLECT,
        input_data={
            "retrieved_chunk_count": len(state["retrieved_chunks"]),
            "retry_count": state["retry_count"],
        },
        output_data=reflection,
    )
    return {
        "reflection": reflection,
        "retrieval_query": retrieval_query,
        "ai_mode": get_ai_mode(),
    }


def route_after_reflection(state: ResearchAgentState) -> Literal["retry", "final"]:
    if state["reflection"].get("enough_evidence"):
        return "final"
    if state["retry_count"] < 1:
        return "retry"
    return "final"


def final_node(state: ResearchAgentState) -> dict[str, Any]:
    synthesis = synthesize_final_answer(state["user_query"], state["retrieved_chunks"])
    final_answer = synthesis["answer"]
    enough_evidence = state["reflection"].get("enough_evidence", False)
    confidence = STRONG_EVIDENCE_CONFIDENCE if enough_evidence else WEAK_EVIDENCE_CONFIDENCE
    if not enough_evidence:
        final_answer = _compose_low_evidence_answer(state["retrieved_chunks"])
    errors = list(state["errors"])
    if synthesis["error"]:
        errors.append(synthesis["error"])

    _create_step(
        state,
        AgentStep.StepType.FINAL,
        input_data={
            "query": state["user_query"],
            "chunk_ids": [chunk["chunk_id"] for chunk in state["retrieved_chunks"]],
            "ai_mode": get_ai_mode(),
            "retry_count": state["retry_count"],
        },
        output_data={
            "final_answer": final_answer,
            "confidence_score": confidence,
            "ai_mode": synthesis["ai_mode"],
            "model": synthesis["model"],
            "error": synthesis["error"],
            "evidence": state["retrieved_chunks"],
            "retry_count": state["retry_count"],
        },
    )
    return {
        "final_answer": final_answer,
        "confidence_score": confidence,
        "ai_mode": synthesis["ai_mode"],
        "errors": errors,
    }


def _create_step(
    state: ResearchAgentState,
    step_type: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
) -> None:
    AgentStep.objects.create(
        research_run_id=state["research_run_id"],
        step_type=step_type,
        input_data=input_data,
        output_data=output_data,
    )


def _is_retry_retrieval(state: ResearchAgentState) -> bool:
    return bool(state["reflection"]) and not state["reflection"].get("enough_evidence", False)


def _top_retrieval_score(chunks: list[dict[str, Any]]) -> float:
    scores = [
        float(chunk["score"])
        for chunk in chunks
        if isinstance(chunk.get("score"), (int, float))
    ]
    return max(scores, default=0.0)


def _build_retry_query(user_query: str) -> str:
    return f"{user_query} market evidence trends data sources"


def _compose_low_evidence_answer(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return (
            "The current document collection does not contain enough evidence to answer "
            "this question confidently. Upload relevant sources and try again."
        )
    return (
        "The uploaded sources do not contain enough relevant evidence to answer this "
        "question confidently. Add more directly related sources and try again."
    )
