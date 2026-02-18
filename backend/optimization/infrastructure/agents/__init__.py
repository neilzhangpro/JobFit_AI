"""LangGraph AI Agents for the optimization pipeline.

Exports the BaseAgent ABC, state schema types, routing helpers,
graph builder, and agent implementations (JDAnalyzerAgent, etc.).
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
from optimization.infrastructure.agents.jd_analyzer import (
    JDAnalyzerAgent,
    jd_analyzer_node,
)

__all__ = [
    # Base class
    "BaseAgent",
    # Agents
    "JDAnalyzerAgent",
    "jd_analyzer_node",
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
