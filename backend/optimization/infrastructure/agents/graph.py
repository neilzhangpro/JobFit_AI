"""LangGraph state schema, routing logic, and graph builder.

Defines the ``OptimizationState`` TypedDict that flows through every
node, the ``score_check_router`` conditional edge, the
``result_aggregator_node`` final assembly step, and
``build_optimization_graph`` which wires them into a compiled
LangGraph ``StateGraph``.

Architecture reference: docs/07-ai-workflow-architecture.md §2, §4.
"""

from collections.abc import Callable
from typing import Any, TypedDict, cast

# ------------------------------------------------------------------
# Structured sub-types used inside OptimizationState
# ------------------------------------------------------------------


class JDAnalysisDict(TypedDict):
    """Structured output from the JD Analyzer agent."""

    hard_skills: list[str]
    soft_skills: list[str]
    responsibilities: list[str]
    qualifications: list[str]
    keyword_weights: dict[str, float]


class ResumeChunkDict(TypedDict):
    """A single retrieved resume chunk from the vector store."""

    section_type: str
    content: str
    relevance_score: float


class ScoreBreakdownDict(TypedDict):
    """Per-category ATS score breakdown."""

    keywords: float
    skills: float
    experience: float
    formatting: float


class GapReportDict(TypedDict):
    """Structured output from the Gap Analyzer agent."""

    missing_skills: list[str]
    recommendations: list[str]
    transferable_skills: list[str]
    priority: dict[str, str]


class AgentErrorDict(TypedDict):
    """Record of an error during pipeline execution."""

    agent_name: str
    error_type: str
    error_message: str
    recoverable: bool


# ------------------------------------------------------------------
# Main pipeline state
# ------------------------------------------------------------------


class OptimizationState(TypedDict, total=False):
    """Shared state passed through the LangGraph state machine.

    Fields marked *input* are set before graph invocation.
    Fields marked *output* are written by specific agent nodes.
    ``total=False`` makes every field optional so partial updates work.
    """

    # --- Inputs (set by Application Layer) ---
    tenant_id: str
    user_id: str
    session_id: str
    jd_text: str
    resume_sections: list[dict[str, Any]]

    # --- JD Analysis (JDAnalyzerAgent) ---
    jd_analysis: JDAnalysisDict

    # --- Retrieval (RAGRetrieverAgent) ---
    relevant_chunks: list[ResumeChunkDict]

    # --- Rewriting (ResumeRewriterAgent) ---
    optimized_sections: dict[str, list[str]]
    rewrite_attempts: int

    # --- Scoring (ATSScorerAgent) ---
    ats_score: float
    score_breakdown: ScoreBreakdownDict

    # --- Gap Analysis (GapAnalyzerAgent) ---
    gap_report: GapReportDict

    # --- Pipeline Control ---
    score_threshold: float
    max_rewrite_attempts: int
    current_node: str
    errors: list[AgentErrorDict]

    # --- Token Tracking ---
    token_usage: dict[str, int]
    total_tokens_used: int

    # --- Final Output ---
    final_result: dict[str, Any]


# ------------------------------------------------------------------
# Conditional routing
# ------------------------------------------------------------------


def score_check_router(state: dict[str, Any]) -> str:
    """Decide whether to retry rewriting or proceed to gap analysis.

    Decision logic:
        * ``ats_score >= threshold`` → ``"proceed_to_gap"``
        * ``ats_score < threshold AND attempts < max`` →
          ``"retry_rewrite"``
        * ``ats_score < threshold AND attempts >= max`` →
          ``"proceed_to_gap"`` (exhausted retries, use best result)

    Args:
        state: Current pipeline state.

    Returns:
        ``"retry_rewrite"`` or ``"proceed_to_gap"`` routing key.
    """
    ats_score: float = state.get("ats_score", 0.0)
    threshold: float = state.get("score_threshold", 0.75)
    attempts: int = state.get("rewrite_attempts", 0)
    max_attempts: int = state.get("max_rewrite_attempts", 2)

    if ats_score >= threshold:
        return "proceed_to_gap"

    if attempts < max_attempts:
        return "retry_rewrite"

    # Exhausted retries — proceed with best available result
    return "proceed_to_gap"


# ------------------------------------------------------------------
# Result aggregation node
# ------------------------------------------------------------------


def result_aggregator_node(
    state: OptimizationState,
) -> dict[str, Any]:
    """Assemble all pipeline outputs into the final result.

    This node performs **no LLM calls** — it is a pure data
    assembly step that collects outputs from prior nodes.

    Args:
        state: Current pipeline state after all agents have run.

    Returns:
        Partial state update with ``final_result`` and
        ``total_tokens_used``.
    """
    token_usage: dict[str, int] = state.get("token_usage", {})
    return {
        "final_result": {
            "jd_analysis": state.get("jd_analysis", {}),
            "optimized_sections": state.get("optimized_sections", {}),
            "ats_score": state.get("ats_score", 0.0),
            "score_breakdown": state.get("score_breakdown", {}),
            "gap_report": state.get("gap_report", {}),
            "rewrite_attempts": state.get("rewrite_attempts", 0),
            "total_tokens_used": state.get("total_tokens_used", 0),
            "token_usage": token_usage,
            "errors": state.get("errors", []),
        },
        "total_tokens_used": sum(token_usage.values()),
    }


# ------------------------------------------------------------------
# Stub node functions (replaced by real agents in later PRs)
# ------------------------------------------------------------------


def _stub_node(
    name: str,
) -> Callable[[OptimizationState], dict[str, Any]]:
    """Create a pass-through stub for an agent node.

    Each stub sets ``current_node`` so integration tests can
    verify graph wiring before real agents are implemented.
    """

    def _node(state: OptimizationState) -> dict[str, Any]:
        return {"current_node": name}

    _node.__name__ = name
    _node.__qualname__ = name
    return _node


# ------------------------------------------------------------------
# Graph builder
# ------------------------------------------------------------------


def build_optimization_graph():  # type: ignore[no-untyped-def]
    """Build and compile the optimization pipeline state graph.

    Nodes are registered as stubs in this PR; each subsequent
    agent PR replaces one stub with its real implementation.

    Returns:
        A compiled ``StateGraph`` ready for ``.invoke()``.
    """
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(OptimizationState)

    # --- Register nodes ---
    from optimization.infrastructure.agents.jd_analyzer import (
        jd_analyzer_node,
    )
    from optimization.infrastructure.agents.rag_retriever import (
        rag_retriever_node,
    )

    # Cast nodes to satisfy LangGraph's strict add_node overloads
    nodes: dict[str, Any] = {
        "jd_analysis": jd_analyzer_node,
        "resume_retrieval": rag_retriever_node,
        "resume_rewriting": _stub_node("resume_rewriting"),
        "ats_scoring": _stub_node("ats_scoring"),
        "gap_analysis": _stub_node("gap_analysis"),
        "result_aggregation": result_aggregator_node,
    }
    for node_name, node_fn in nodes.items():
        graph.add_node(node_name, cast(Any, node_fn))

    # --- Define edges ---
    graph.add_edge(START, "jd_analysis")
    graph.add_edge("jd_analysis", "resume_retrieval")
    graph.add_edge("resume_retrieval", "resume_rewriting")
    graph.add_edge("resume_rewriting", "ats_scoring")

    # Conditional: score check determines next step
    graph.add_conditional_edges(
        "ats_scoring",
        score_check_router,
        {
            "retry_rewrite": "resume_rewriting",
            "proceed_to_gap": "gap_analysis",
        },
    )

    graph.add_edge("gap_analysis", "result_aggregation")
    graph.add_edge("result_aggregation", END)

    return graph.compile()
