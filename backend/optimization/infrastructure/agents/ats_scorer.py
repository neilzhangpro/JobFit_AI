"""ATSScorerAgent — evaluates ATS compatibility of optimized resume vs JD.

Fourth agent in the optimization pipeline. Uses optional rule-based pre-scorer
(keyword overlap, formatting checks); falls back to GPT-4o-mini for full
breakdown when rule-based confidence is below threshold. Writes ats_score and
score_breakdown to state. Model and threshold from Settings.
"""

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from optimization.infrastructure.agents.base_agent import BaseAgent
from optimization.infrastructure.agents.graph import (
    JDAnalysisDict,
    ScoreBreakdownDict,
)
from shared.domain.exceptions import AgentExecutionError, ValidationError

_WEIGHTS = {"keywords": 0.35, "skills": 0.30, "experience": 0.25, "formatting": 0.10}

_SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) scoring engine.
Evaluate the optimized resume sections (experience, skills summary, projects)
against the target JD requirements. Score each category from 0.0 to 1.0
and provide an overall weighted score.

Scoring categories and weights:
- keywords (0.35): How many JD keywords appear in the resume bullets?
- skills (0.30): How well do the demonstrated skills match JD requirements?
- experience (0.25): How relevant is the experience to JD responsibilities?
- formatting (0.10): Are bullets clear, concise, and ATS-parseable?

Respond ONLY with valid JSON. No markdown, no explanation.
{
  "overall": 0.0-1.0,
  "keywords": 0.0-1.0,
  "skills": 0.0-1.0,
  "experience": 0.0-1.0,
  "formatting": 0.0-1.0
}"""


def _clamp(value: float) -> float:
    """Clamp score to [0.0, 1.0]."""
    if not isinstance(value, (int, float)):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _rule_based_keyword_score(
    jd_analysis: JDAnalysisDict,
    optimized_sections: dict[str, list[str]],
) -> float:
    """Compute keyword overlap score: share of JD keywords found in optimized text."""
    keywords: set[str] = set()
    for key in ("hard_skills", "soft_skills", "responsibilities", "qualifications"):
        raw = jd_analysis.get(key)
        items: list[str] = raw if isinstance(raw, list) else []
        for item in items:
            if isinstance(item, str) and item.strip():
                keywords.add(item.strip().lower())
    weights_raw = jd_analysis.get("keyword_weights")
    weights: dict[str, float] = weights_raw if isinstance(weights_raw, dict) else {}
    for k in weights:
        if isinstance(k, str) and k.strip():
            keywords.add(k.strip().lower())
    if not keywords:
        return 0.5
    text_parts: list[str] = []
    for bullets in optimized_sections.values():
        if isinstance(bullets, list):
            text_parts.extend(str(b).lower() for b in bullets)
    text = " ".join(text_parts)
    found = sum(1 for kw in keywords if kw in text)
    return found / len(keywords) if keywords else 0.5


def _rule_based_formatting_score(optimized_sections: dict[str, list[str]]) -> float:
    """Simple formatting score: bullets present, reasonable length."""
    total_bullets = 0
    ok_length = 0
    for bullets in optimized_sections.values():
        if not isinstance(bullets, list):
            continue
        for b in bullets:
            s = str(b).strip()
            total_bullets += 1
            if 10 <= len(s) <= 500:
                ok_length += 1
    if total_bullets == 0:
        return 0.5
    return ok_length / total_bullets


def _rule_based_scores(
    jd_analysis: JDAnalysisDict,
    optimized_sections: dict[str, list[str]],
) -> tuple[float, ScoreBreakdownDict]:
    """Rule-based keyword/formatting scores; skills/experience default 0.5."""
    kw = _rule_based_keyword_score(jd_analysis, optimized_sections)
    fmt = _rule_based_formatting_score(optimized_sections)
    breakdown: ScoreBreakdownDict = {
        "keywords": _clamp(kw),
        "skills": 0.5,
        "experience": 0.5,
        "formatting": _clamp(fmt),
    }
    overall = (
        _WEIGHTS["keywords"] * breakdown["keywords"]
        + _WEIGHTS["skills"] * breakdown["skills"]
        + _WEIGHTS["experience"] * breakdown["experience"]
        + _WEIGHTS["formatting"] * breakdown["formatting"]
    )
    return _clamp(overall), breakdown


class ATSScorerAgent(BaseAgent):
    """Scores ATS compatibility of optimized_sections vs jd_analysis.

    Uses rule-based pre-scorer when confidence is high; otherwise calls LLM.
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_token_count: int = 0

    def prepare(self, state: dict[str, Any]) -> str:
        """Build user prompt from jd_analysis and optimized_sections.

        Args:
            state: Must contain jd_analysis and optimized_sections.

        Returns:
            User message content for LLM.

        Raises:
            ValidationError: If required state keys are missing.
        """
        jd_analysis = state.get("jd_analysis")
        optimized_sections = state.get("optimized_sections")
        if not jd_analysis or not isinstance(jd_analysis, dict):
            raise ValidationError("ATSScorerAgent requires jd_analysis from prior node")
        if not optimized_sections or not isinstance(optimized_sections, dict):
            raise ValidationError(
                "ATSScorerAgent requires optimized_sections from Resume Rewriter"
            )
        jd: JDAnalysisDict = jd_analysis
        sections_str = json.dumps(optimized_sections, indent=2)
        return f"""## JD Requirements
Hard Skills: {jd.get("hard_skills", [])}
Soft Skills: {jd.get("soft_skills", [])}
Responsibilities: {jd.get("responsibilities", [])}
Keyword Weights: {jd.get("keyword_weights", {{}})}

## Optimized Resume Sections
{sections_str}

Score each category 0.0-1.0 and return JSON with keys: overall, keywords,
skills, experience, formatting."""

    def execute(self, prompt: str) -> str:
        """Call LLM and return raw JSON. Sets _last_token_count from metadata."""
        settings = get_settings()
        model = self._get_model(
            model_name=settings.ats_scorer_model,
            temperature=settings.ats_scorer_temperature,
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = model.invoke(messages)
        metadata: dict[str, Any] = getattr(response, "response_metadata", {}) or {}
        self._last_token_count = self._track_tokens(metadata, "ats_scorer")
        content = response.content if hasattr(response, "content") else response
        return content if isinstance(content, str) else str(content)

    def parse_output(self, raw_output: str) -> dict[str, Any]:
        """Parse JSON and clamp all scores to [0.0, 1.0].

        Returns ats_score and score_breakdown (ScoreBreakdownDict).
        """
        raw_clean = raw_output.strip()
        if raw_clean.startswith("```"):
            raw_clean = re.sub(r"^```\w*\n?", "", raw_clean)
            raw_clean = re.sub(r"\n?```\s*$", "", raw_clean)
        try:
            data = json.loads(raw_clean)
        except json.JSONDecodeError as e:
            raise AgentExecutionError(
                agent_name="ATSScorerAgent",
                message=f"Invalid JSON from LLM: {e!s}",
            ) from e
        if not isinstance(data, dict):
            raise AgentExecutionError(
                agent_name="ATSScorerAgent",
                message="LLM output is not a JSON object",
            )
        breakdown: ScoreBreakdownDict = {
            "keywords": _clamp(data.get("keywords", 0.5)),
            "skills": _clamp(data.get("skills", 0.5)),
            "experience": _clamp(data.get("experience", 0.5)),
            "formatting": _clamp(data.get("formatting", 0.5)),
        }
        overall = data.get("overall")
        if overall is None:
            overall = (
                _WEIGHTS["keywords"] * breakdown["keywords"]
                + _WEIGHTS["skills"] * breakdown["skills"]
                + _WEIGHTS["experience"] * breakdown["experience"]
                + _WEIGHTS["formatting"] * breakdown["formatting"]
            )
        ats_score = _clamp(overall)
        return {
            "ats_score": ats_score,
            "score_breakdown": breakdown,
        }

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run agent: try rule-based first; if confidence below threshold, call LLM."""
        settings = get_settings()
        jd_analysis = state.get("jd_analysis")
        optimized_sections = state.get("optimized_sections") or {}
        if not jd_analysis or not isinstance(jd_analysis, dict):
            raise ValidationError("ATSScorerAgent requires jd_analysis from prior node")
        if not optimized_sections or not isinstance(optimized_sections, dict):
            raise ValidationError(
                "ATSScorerAgent requires optimized_sections from Resume Rewriter"
            )
        jd: JDAnalysisDict = jd_analysis
        threshold = settings.ats_scorer_rule_confidence_threshold
        rule_overall, rule_breakdown = _rule_based_scores(jd, optimized_sections)
        if rule_overall >= threshold:
            existing_usage = state.get("token_usage") or {}
            return {
                "ats_score": rule_overall,
                "score_breakdown": rule_breakdown,
                "token_usage": {**existing_usage, "ats_scorer": 0},
            }
        result = super().run(state)
        existing_usage = state.get("token_usage") or {}
        result["token_usage"] = {
            **existing_usage,
            "ats_scorer": self._last_token_count,
        }
        return result


def ats_scorer_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node that runs the ATS Scorer agent.

    Args:
        state: Current OptimizationState (jd_analysis, optimized_sections required).

    Returns:
        Partial state update with ats_score, score_breakdown, token_usage.
    """
    agent = ATSScorerAgent()
    return agent.run(state)
