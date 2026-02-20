"""RAGRetrieverAgent — retrieves relevant resume chunks via vector search.

Second agent in the optimization pipeline. Pure ChromaDB similarity search —
no LLM call, zero token cost. Bridges Resume context (vector store) and
Optimization context (downstream rewriter).

Configuration from Settings: rag_retriever_top_k, rag_retriever_relevance_threshold.
"""

import json
from typing import Any, Protocol

from config import get_settings
from optimization.infrastructure.agents.base_agent import BaseAgent
from optimization.infrastructure.agents.graph import (
    JDAnalysisDict,
    ResumeChunkDict,
)
from shared.domain.exceptions import AgentExecutionError, ValidationError


class VectorStoreReader(Protocol):
    """Read-only interface for querying resume embeddings.

    Implemented by resume context's VectorStoreAdapter.
    """

    def search(
        self,
        tenant_id: str,
        query: str,
        k: int = 10,
        resume_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for resume sections similar to query.

        Returns:
            List of dicts with ``content``, ``metadata``, ``relevance_score``.
        """
        ...


def _default_vector_store() -> VectorStoreReader:
    """Create VectorStoreReader using application settings."""
    from resume.infrastructure.vector_store import VectorStoreAdapter

    return VectorStoreAdapter(get_settings())


def _build_query_from_jd(jd_analysis: JDAnalysisDict) -> str:
    """Build search query from JD analysis keywords.

    Concatenates hard_skills, soft_skills, and keyword_weights keys
    into a single query string for vector similarity search.

    Args:
        jd_analysis: Structured output from JDAnalyzerAgent.

    Returns:
        Space-separated query string (e.g. "Python AWS Docker leadership").
    """
    parts: list[str] = []

    hard_skills = jd_analysis.get("hard_skills") or []
    soft_skills = jd_analysis.get("soft_skills") or []
    keyword_weights = jd_analysis.get("keyword_weights") or {}

    for skill in hard_skills:
        if skill and isinstance(skill, str):
            parts.append(str(skill))
    for skill in soft_skills:
        if skill and isinstance(skill, str) and skill not in parts:
            parts.append(str(skill))
    for kw in keyword_weights:
        if kw and isinstance(kw, str) and kw not in parts:
            parts.append(str(kw))

    return " ".join(parts) if parts else ""


def _raw_to_chunks(
    raw_results: list[dict[str, Any]],
    relevance_threshold: float,
) -> list[ResumeChunkDict]:
    """Convert raw search results to ResumeChunkDict, filter and deduplicate.

    Args:
        raw_results: List from VectorStoreAdapter.search().
        relevance_threshold: Min score to include (discard low-similarity noise).

    Returns:
        Deduplicated list of ResumeChunkDict, sorted by relevance descending.
    """
    seen_content: set[str] = set()
    chunks: list[ResumeChunkDict] = []

    for item in raw_results:
        content = (item.get("content") or "").strip()
        score = float(item.get("relevance_score", 0.0))
        if score < relevance_threshold:
            continue
        if not content or content in seen_content:
            continue
        seen_content.add(content)

        metadata = item.get("metadata") or {}
        section_type = str(metadata.get("section_type", "unknown"))

        chunks.append(
            ResumeChunkDict(
                section_type=section_type,
                content=content,
                relevance_score=round(score, 4),
            )
        )

    # Sort by relevance descending
    chunks.sort(key=lambda c: c["relevance_score"], reverse=True)
    return chunks


class RAGRetrieverAgent(BaseAgent):
    """Retrieves relevant resume chunks via ChromaDB vector similarity search."""

    def __init__(self, vector_store: VectorStoreReader | None = None) -> None:
        super().__init__()
        self._vector_store = vector_store or _default_vector_store()
        self._tenant_id = ""

    def prepare(self, state: dict[str, Any]) -> str:
        """Validate state and build query from JD analysis.

        Args:
            state: Must contain ``tenant_id`` and ``jd_analysis``.

        Returns:
            Query string for vector search.

        Raises:
            ValidationError: If ``tenant_id`` or ``jd_analysis`` missing.
        """
        tenant_id = (state.get("tenant_id") or "").strip()
        if not tenant_id:
            raise ValidationError("RAGRetrieverAgent requires tenant_id in state")

        jd_analysis = state.get("jd_analysis")
        if not jd_analysis or not isinstance(jd_analysis, dict):
            raise ValidationError(
                "RAGRetrieverAgent requires jd_analysis from prior node"
            )

        self._tenant_id = tenant_id
        query = _build_query_from_jd(jd_analysis)

        if not query.strip():
            self._logger.warning("JD analysis has no keywords — using fallback query")
            query = "experience skills projects"

        return query

    def execute(self, prompt: str) -> str:
        """Query ChromaDB and return serialized chunks.

        No LLM call — pure vector search. Returns JSON list of chunks.
        """
        settings = get_settings()
        top_k = settings.rag_retriever_top_k

        raw = self._vector_store.search(
            tenant_id=self._tenant_id,
            query=prompt,
            k=top_k,
        )

        if not raw:
            self._logger.warning(
                "ChromaDB returned zero results for tenant %s — "
                "resume rewriter will use resume_sections fallback",
                self._tenant_id,
            )

        # Serialize for parse_output contract
        return json.dumps(raw, default=str)

    def parse_output(self, raw_output: str) -> dict[str, Any]:
        """Parse and filter chunks into state update.

        Args:
            raw_output: JSON string from execute().

        Returns:
            Partial state update with ``relevant_chunks`` key.

        Raises:
            AgentExecutionError: If JSON is invalid.
        """
        try:
            raw_list = json.loads(raw_output)
        except json.JSONDecodeError as e:
            raise AgentExecutionError(
                agent_name="RAGRetrieverAgent",
                message=f"Invalid JSON from vector store: {e!s}",
            ) from e

        if not isinstance(raw_list, list):
            raise AgentExecutionError(
                agent_name="RAGRetrieverAgent",
                message="Vector store output is not a list",
            )

        settings = get_settings()
        threshold = settings.rag_retriever_relevance_threshold

        chunks = _raw_to_chunks(raw_list, threshold)

        return {"relevant_chunks": chunks}


def rag_retriever_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node that runs the RAG Retriever agent.

    Args:
        state: Current OptimizationState (must include ``tenant_id``,
            ``jd_analysis`` from prior node).

    Returns:
        Partial state update with ``relevant_chunks``.
    """
    agent = RAGRetrieverAgent()
    return agent.run(state)
