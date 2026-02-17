"""LangGraph AI Agents for the optimization pipeline.

Exports the BaseAgent ABC, state schema types, routing helpers,
and the graph builder.  Individual agent classes (JDAnalyzerAgent,
etc.) will be added by subsequent PRs.
"""

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

__all__ = [
    # Base class
    "BaseAgent",
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
