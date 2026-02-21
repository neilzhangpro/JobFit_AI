"""LangGraph AI Agents for the optimization pipeline.

Exports the BaseAgent ABC, state schema types, routing helpers,
graph builder, and agent implementations (JDAnalyzerAgent, etc.).

LLM-dependent agents (jd_analyzer) are imported lazily so that
RAG-only tests can run without langchain_openai/langchain_core.
"""

from typing import Any

from optimization.infrastructure.agents.base_agent import BaseAgent
from optimization.infrastructure.agents.graph import (
    AgentErrorDict,
    GapReportDict,
    JDAnalysisDict,
    OptimizationState,
    ResumeChunkDict,
    ScoreBreakdownDict,
    build_optimization_graph,
    result_aggregator_node,
    score_check_router,
)


def __getattr__(name: str) -> Any:
    """Lazy-load agent modules so RAG tests can run without LLM deps."""
    if name in ("JDAnalyzerAgent", "jd_analyzer_node"):
        from optimization.infrastructure.agents import jd_analyzer

        return getattr(jd_analyzer, name)
    if name in ("RAGRetrieverAgent", "rag_retriever_node"):
        from optimization.infrastructure.agents import rag_retriever

        return getattr(rag_retriever, name)
    if name in ("ATSScorerAgent", "ats_scorer_node"):
        from optimization.infrastructure.agents import ats_scorer

        return getattr(ats_scorer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base class
    "BaseAgent",
    # Agents
    "JDAnalyzerAgent",
    "jd_analyzer_node",
    "RAGRetrieverAgent",
    "rag_retriever_node",
    "ATSScorerAgent",
    "ats_scorer_node",
    # State schema types
    "OptimizationState",
    "JDAnalysisDict",
    "ResumeChunkDict",
    "ScoreBreakdownDict",
    "GapReportDict",
    "AgentErrorDict",
    # Graph helpers
    "score_check_router",
    "result_aggregator_node",
    "build_optimization_graph",
]
