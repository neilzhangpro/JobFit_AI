"""ResumeRewriterAgent — rewrites experience, skills_summary, projects via LLM.

Third agent in the optimization pipeline. Uses GPT-4o to align resume sections
with JD keywords. Supports first attempt and retry prompt with ATS score feedback.
Model and context limits from Settings.
"""

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from optimization.infrastructure.agents.base_agent import BaseAgent
from optimization.infrastructure.agents.graph import (
    JDAnalysisDict,
    ResumeChunkDict,
)
from shared.domain.exceptions import AgentExecutionError, ValidationError

_SECTION_KEYS = ("experience", "skills_summary", "projects")

_SYSTEM_PROMPT_BASE = """You are an expert resume writer and ATS optimization
specialist. Rewrite the candidate's resume sections to maximize alignment with the
target job description. You will optimize three section types:

1. EXPERIENCE — Rewrite bullet points:
   - Embed relevant JD keywords naturally (do NOT keyword-stuff).
   - Start each bullet with a strong action verb.
   - Quantify achievements with numbers, percentages, or dollar amounts.

2. SKILLS SUMMARY — Rewrite the skills/profile section:
   - Reorder skills to lead with the highest-weighted JD keywords.
   - Add JD-required skills the candidate possesses but did not list.
   - Remove or de-emphasize skills irrelevant to this JD.
   - Keep as a concise list or 2-3 sentence summary.

3. PROJECTS — Rewrite project descriptions (if present):
   - Emphasize JD-relevant technologies, outcomes, and scale.
   - Quantify impact where possible.

General rules for ALL sections:
- Preserve factual accuracy — do NOT fabricate experiences or skills.
- Maintain professional tone appropriate for ATS systems.

Respond ONLY with valid JSON. No markdown, no explanation."""

_RETRY_SUFFIX_TEMPLATE = """

The previous rewrite scored {ats_score:.0%} on ATS compatibility.
Score breakdown: keywords={keywords:.0%}, skills={skills:.0%},
experience={experience:.0%}, formatting={formatting:.0%}.

Focus on improving the weakest categories. Specifically:
- If keywords score is low: integrate more JD-specific terminology.
- If skills score is low: strengthen the skills summary.
- If experience score is low: strengthen relevance in experience bullets.
- If formatting score is low: use cleaner structure in all sections."""


def _format_chunks_by_section(
    chunks: list[ResumeChunkDict],
    top_k: int,
    max_chars: int,
) -> str:
    """Group chunks by section_type and format for the user prompt."""
    by_section: dict[str, list[str]] = {}
    for c in chunks[:top_k]:
        content = (c.get("content") or "").strip()
        if not content:
            continue
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        st = (c.get("section_type") or "other").strip() or "other"
        # Normalize to our section keys
        if st == "skills":
            st = "skills_summary"
        if st not in by_section:
            by_section[st] = []
        by_section[st].append(content)

    lines: list[str] = []
    for key in _SECTION_KEYS:
        if key in by_section and by_section[key]:
            lines.append(f"### {key.replace('_', ' ').title()}")
            for block in by_section[key]:
                lines.append(block)
            lines.append("")
    return "\n".join(lines).strip() if lines else ""


def _sections_from_resume_sections(sections: list[dict[str, Any]]) -> str:
    """Format resume_sections (from state) as content by section."""
    by_section: dict[str, list[str]] = {}
    for s in sections:
        if not isinstance(s, dict):
            continue
        st = (s.get("type") or s.get("section_type") or "other").strip() or "other"
        if st == "skills":
            st = "skills_summary"
        content = (s.get("content") or "").strip()
        if content:
            if st not in by_section:
                by_section[st] = []
            by_section[st].append(content)

    lines: list[str] = []
    for key in _SECTION_KEYS:
        if key in by_section and by_section[key]:
            lines.append(f"### {key.replace('_', ' ').title()}")
            for block in by_section[key]:
                lines.append(block)
            lines.append("")
    return "\n".join(lines).strip() if lines else ""


def _ensure_str_list(value: Any) -> list[str]:
    """Ensure value is a list of strings."""
    if isinstance(value, list):
        return [str(x).strip() for x in value if x is not None]
    return [str(value).strip()] if value is not None else []


class ResumeRewriterAgent(BaseAgent):
    """Rewrites experience, skills_summary, and projects to align with JD."""

    def __init__(self) -> None:
        super().__init__()
        self._last_token_count: int = 0
        self._system_prompt: str = _SYSTEM_PROMPT_BASE

    def prepare(self, state: dict[str, Any]) -> str:
        """Build user prompt and set system prompt (with optional retry suffix).

        Args:
            state: Must contain ``jd_analysis`` and either ``relevant_chunks``
                or ``resume_sections``.

        Returns:
            User message content (JD requirements + candidate content).

        Raises:
            ValidationError: If jd_analysis or content source is missing.
        """
        settings = get_settings()
        jd_analysis = state.get("jd_analysis")
        if not jd_analysis or not isinstance(jd_analysis, dict):
            raise ValidationError(
                "ResumeRewriterAgent requires jd_analysis from prior node"
            )

        chunks: list[ResumeChunkDict] = state.get("relevant_chunks") or []
        resume_sections: list[dict[str, Any]] = state.get("resume_sections") or []

        if chunks:
            content_block = _format_chunks_by_section(
                chunks,
                top_k=settings.resume_rewriter_top_k_chunks,
                max_chars=settings.resume_rewriter_max_chunk_chars,
            )
        elif resume_sections:
            content_block = _sections_from_resume_sections(resume_sections)
        else:
            raise ValidationError(
                "ResumeRewriterAgent requires relevant_chunks or resume_sections"
            )

        if not content_block.strip():
            raise ValidationError(
                "ResumeRewriterAgent: no content in chunks or resume_sections"
            )

        # Retry: append score feedback to system prompt
        self._system_prompt = _SYSTEM_PROMPT_BASE
        attempts = state.get("rewrite_attempts") or 0
        ats_score = state.get("ats_score")
        score_breakdown = state.get("score_breakdown")

        if attempts > 0 and ats_score is not None and score_breakdown:
            breakdown = score_breakdown if isinstance(score_breakdown, dict) else {}
            self._system_prompt += _RETRY_SUFFIX_TEMPLATE.format(
                ats_score=float(ats_score),
                keywords=breakdown.get("keywords", 0.0),
                skills=breakdown.get("skills", 0.0),
                experience=breakdown.get("experience", 0.0),
                formatting=breakdown.get("formatting", 0.0),
            )

        jd: JDAnalysisDict = jd_analysis

        def _join(items: object) -> str:
            if isinstance(items, list):
                return ", ".join(str(x) for x in items if x) or "(none)"
            return str(items) if items else "(none)"

        kw_weights = jd.get("keyword_weights") or {}
        kw_str = ", ".join(f"{k}: {v}" for k, v in kw_weights.items()) or "(none)"
        user_prompt = f"""## Target JD Requirements
Hard Skills: {_join(jd.get("hard_skills"))}
Soft Skills: {_join(jd.get("soft_skills"))}
Key Responsibilities: {_join(jd.get("responsibilities"))}
Keyword Weights: {kw_str}

## Candidate's Relevant Content
{content_block}

Rewrite the sections. Return a JSON object with section keys:
"experience", "skills_summary", "projects" (only include keys for sections
present above)."""
        return user_prompt

    def execute(self, prompt: str) -> str:
        """Call LLM and return raw JSON.

        Sets ``_last_token_count`` from response metadata.
        """
        settings = get_settings()
        model = self._get_model(
            model_name=settings.resume_rewriter_model,
            temperature=settings.resume_rewriter_temperature,
        )
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=prompt),
        ]
        response = model.invoke(messages)
        metadata: dict[str, Any] = getattr(response, "response_metadata", {}) or {}
        self._last_token_count = self._track_tokens(metadata, "resume_rewriter")
        content = response.content if hasattr(response, "content") else response
        return content if isinstance(content, str) else str(content)

    def parse_output(self, raw_output: str) -> dict[str, Any]:
        """Parse and validate JSON into optimized_sections.

        Strips markdown code fences before parsing. Returns only keys that
        are in _SECTION_KEYS and present in output.
        """
        raw_clean = raw_output.strip()
        if raw_clean.startswith("```"):
            raw_clean = re.sub(r"^```\w*\n?", "", raw_clean)
            raw_clean = re.sub(r"\n?```\s*$", "", raw_clean)
        try:
            data = json.loads(raw_clean)
        except json.JSONDecodeError as e:
            raise AgentExecutionError(
                agent_name="ResumeRewriterAgent",
                message=f"Invalid JSON from LLM: {e!s}",
            ) from e

        if not isinstance(data, dict):
            raise AgentExecutionError(
                agent_name="ResumeRewriterAgent",
                message="LLM output is not a JSON object",
            )

        optimized: dict[str, list[str]] = {}
        for key in _SECTION_KEYS:
            if key in data and data[key] is not None:
                optimized[key] = _ensure_str_list(data[key])

        return {"optimized_sections": optimized}

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run agent, merge token_usage, and increment rewrite_attempts."""
        result = super().run(state)
        existing_usage = state.get("token_usage") or {}
        result["token_usage"] = {
            **existing_usage,
            "resume_rewriter": self._last_token_count,
        }
        result["rewrite_attempts"] = (state.get("rewrite_attempts") or 0) + 1
        return result


def resume_rewriter_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node that runs the Resume Rewriter agent.

    Args:
        state: Current OptimizationState (jd_analysis, relevant_chunks or
            resume_sections required).

    Returns:
        Partial state update with ``optimized_sections``, ``rewrite_attempts``,
        and ``token_usage``.
    """
    agent = ResumeRewriterAgent()
    return agent.run(state)
