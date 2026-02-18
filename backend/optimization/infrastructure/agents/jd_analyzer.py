"""JDAnalyzerAgent — extracts structured requirements from raw JD text via LLM.

First agent in the optimization pipeline. Produces JDAnalysisDict that
downstream agents (RAG retriever, rewriter, scorer, gap analyzer) depend on.
Uses GPT-4o-mini with temperature 0.0 for deterministic extraction.
"""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from optimization.infrastructure.agents.base_agent import BaseAgent
from optimization.infrastructure.agents.graph import JDAnalysisDict
from shared.domain.exceptions import AgentExecutionError, ValidationError

# Minimum JD length (aligns with domain validation)
_MIN_JD_LENGTH = 50

_SYSTEM_PROMPT = """You are a job description analysis expert. Extract structured
requirements from the provided JD. Respond ONLY with valid JSON matching the
schema below.

Schema:
{
  "hard_skills": ["string"],
  "soft_skills": ["string"],
  "responsibilities": ["string"],
  "qualifications": ["string"],
  "keyword_weights": { "skill_name": 0.0-1.0 }
}"""


class JDAnalyzerAgent(BaseAgent):
    """Extracts skills, responsibilities, qualifications, keyword_weights from JD."""

    def __init__(self) -> None:
        super().__init__()
        self._last_token_count: int = 0

    def prepare(self, state: dict[str, Any]) -> str:
        """Validate JD text length and build the prompt.

        Args:
            state: Must contain ``jd_text``.

        Returns:
            JD text to send as user message (system prompt is fixed).

        Raises:
            ValidationError: If ``jd_text`` is missing or too short.
        """
        jd_text = (state.get("jd_text") or "").strip()
        if len(jd_text) < _MIN_JD_LENGTH:
            raise ValidationError(
                "JD text is too short or unintelligible "
                f"(minimum {_MIN_JD_LENGTH} characters)"
            )
        return jd_text

    def execute(self, prompt: str) -> str:
        """Call GPT-4o-mini and return raw JSON content.

        Sets ``_last_token_count`` from response metadata for token tracking.
        """
        model = self._get_model(
            model_name="gpt-4o-mini",
            temperature=0.0,
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = model.invoke(messages)
        metadata: dict[str, Any] = getattr(response, "response_metadata", {}) or {}
        self._last_token_count = self._track_tokens(metadata, "jd_analyzer")
        return response.content if hasattr(response, "content") else str(response)

    def parse_output(self, raw_output: str) -> dict[str, Any]:
        """Parse and validate JSON into JDAnalysisDict.

        Args:
            raw_output: Raw string from the LLM.

        Returns:
            Partial state update with ``jd_analysis`` key.

        Raises:
            AgentExecutionError: If JSON is invalid or schema is wrong.
        """
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as e:
            raise AgentExecutionError(
                agent_name="JDAnalyzerAgent",
                message=f"Invalid JSON from LLM: {e!s}",
            ) from e

        if not isinstance(data, dict):
            raise AgentExecutionError(
                agent_name="JDAnalyzerAgent",
                message="LLM output is not a JSON object",
            )

        required = (
            "hard_skills",
            "soft_skills",
            "responsibilities",
            "qualifications",
            "keyword_weights",
        )
        for key in required:
            if key not in data:
                raise AgentExecutionError(
                    agent_name="JDAnalyzerAgent",
                    message=f"Missing required key in output: {key!r}",
                )

        # Normalise to lists and dict
        hard_skills = _ensure_str_list(data["hard_skills"])
        soft_skills = _ensure_str_list(data["soft_skills"])
        responsibilities = _ensure_str_list(data["responsibilities"])
        qualifications = _ensure_str_list(data["qualifications"])
        keyword_weights = _ensure_keyword_weights(data["keyword_weights"])

        jd_analysis: JDAnalysisDict = {
            "hard_skills": hard_skills,
            "soft_skills": soft_skills,
            "responsibilities": responsibilities,
            "qualifications": qualifications,
            "keyword_weights": keyword_weights,
        }
        return {"jd_analysis": jd_analysis}

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run the agent and merge token_usage into the result."""
        result = super().run(state)
        existing = state.get("token_usage") or {}
        result["token_usage"] = {
            **existing,
            "jd_analyzer": self._last_token_count,
        }
        return result


def _ensure_str_list(value: Any) -> list[str]:
    """Ensure value is a list of strings."""
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)] if value is not None else []


def _ensure_keyword_weights(value: Any) -> dict[str, float]:
    """Ensure value is a dict mapping str -> float in [0, 1]."""
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in value.items():
        try:
            f = float(v)
            out[str(k)] = max(0.0, min(1.0, f))
        except (TypeError, ValueError):
            continue
    return out


def jd_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node that runs the JD Analyzer agent.

    Args:
        state: Current OptimizationState (must include ``jd_text``).

    Returns:
        Partial state update with ``jd_analysis`` and ``token_usage``.
    """
    agent = JDAnalyzerAgent()
    return agent.run(state)
