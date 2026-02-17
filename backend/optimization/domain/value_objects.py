"""Value objects for the optimization domain.

Immutable, compared-by-value types:
    - SessionStatus  — enum with valid-transition guard
    - ScoreBreakdown — per-category ATS scores (keywords/skills/experience/formatting)
    - JDAnalysis     — structured extraction from a job description
    - ATSScore       — overall score + ScoreBreakdown
    - GapReport      — missing skills, recommendations, transferable skills, priority
"""

from dataclasses import dataclass
from enum import Enum

from shared.domain.base_value_object import BaseValueObject
from shared.domain.exceptions import ValidationError


# ------------------------------------------------------------------
# SessionStatus Enum
# ------------------------------------------------------------------

class SessionStatus(Enum):
    """Lifecycle status of an optimization session.

    Valid transitions:
        PENDING → PROCESSING → COMPLETED
        PENDING → PROCESSING → FAILED
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    # Transition map — kept as a module constant to avoid rebuilding per call
    _TRANSITIONS: dict["SessionStatus", set["SessionStatus"]] = {  # type: ignore[misc]
        "pending": {"processing"},
        "processing": {"completed", "failed"},
        "completed": set(),
        "failed": set(),
    }

    def can_transition_to(self, target: "SessionStatus") -> bool:
        """Check whether moving from *self* to *target* is allowed.

        Args:
            target: The desired next status.

        Returns:
            True if the transition is valid, False otherwise.
        """
        allowed: dict[str, set[str]] = {
            "pending": {"processing"},
            "processing": {"completed", "failed"},
            "completed": set(),
            "failed": set(),
        }
        return target.value in allowed.get(self.value, set())


# ------------------------------------------------------------------
# ScoreBreakdown
# ------------------------------------------------------------------

@dataclass(frozen=True)
class ScoreBreakdown(BaseValueObject):
    """Per-category ATS score breakdown.

    Each field is a float in [0.0, 1.0].
    """

    keywords: float     # Keyword match score
    skills: float       # Skills alignment score
    experience: float   # Experience relevance score
    formatting: float   # ATS formatting compliance score

    def __post_init__(self) -> None:
        """Validate all scores are within [0.0, 1.0]."""
        for name in ("keywords", "skills", "experience", "formatting"):
            val = getattr(self, name)
            if not isinstance(val, (int, float)):
                raise ValidationError(
                    f"ScoreBreakdown.{name} must be a number, got {type(val).__name__}"
                )
            if not 0.0 <= val <= 1.0:
                raise ValidationError(
                    f"ScoreBreakdown.{name} must be between 0.0 and 1.0, got {val}"
                )

    def weighted_overall(self) -> float:
        """Return the weighted overall score.

        Weights: keywords=0.35, skills=0.30, experience=0.25, formatting=0.10
        """
        return (
            self.keywords * 0.35
            + self.skills * 0.30
            + self.experience * 0.25
            + self.formatting * 0.10
        )


# ------------------------------------------------------------------
# JDAnalysis
# ------------------------------------------------------------------

@dataclass(frozen=True)
class JDAnalysis(BaseValueObject):
    """Structured analysis extracted from a job description.

    Uses tuples (not lists) to preserve immutability.
    ``keyword_weights`` stores (keyword, weight) pairs with weight in [0.0, 1.0].
    """

    hard_skills: tuple[str, ...]
    soft_skills: tuple[str, ...]
    responsibilities: tuple[str, ...]
    qualifications: tuple[str, ...]
    keyword_weights: tuple[tuple[str, float], ...]  # (keyword, importance)

    def __post_init__(self) -> None:
        """Validate non-empty fields and weight ranges."""
        if not self.hard_skills:
            raise ValidationError("JDAnalysis.hard_skills must not be empty")
        if not self.soft_skills:
            raise ValidationError("JDAnalysis.soft_skills must not be empty")
        if not self.responsibilities:
            raise ValidationError("JDAnalysis.responsibilities must not be empty")
        if not self.qualifications:
            raise ValidationError("JDAnalysis.qualifications must not be empty")
        for keyword, weight in self.keyword_weights:
            if not 0.0 <= weight <= 1.0:
                raise ValidationError(
                    f"JDAnalysis keyword weight for '{keyword}' must be "
                    f"between 0.0 and 1.0, got {weight}"
                )


# ------------------------------------------------------------------
# ATSScore
# ------------------------------------------------------------------

@dataclass(frozen=True)
class ATSScore(BaseValueObject):
    """Overall ATS compatibility score with per-category breakdown."""

    overall: float            # Weighted score in [0.0, 1.0]
    breakdown: ScoreBreakdown

    def __post_init__(self) -> None:
        """Validate overall score range."""
        if not isinstance(self.overall, (int, float)):
            raise ValidationError(
                f"ATSScore.overall must be a number, got {type(self.overall).__name__}"
            )
        if not 0.0 <= self.overall <= 1.0:
            raise ValidationError(
                f"ATSScore.overall must be between 0.0 and 1.0, got {self.overall}"
            )

    def meets_threshold(self, threshold: float = 0.75) -> bool:
        """Return True if *overall* >= *threshold*."""
        return self.overall >= threshold


# ------------------------------------------------------------------
# GapReport
# ------------------------------------------------------------------

@dataclass(frozen=True)
class GapReport(BaseValueObject):
    """Gap analysis between resume and JD requirements.

    ``priority`` stores (skill, level) pairs where level ∈ {high, medium, low}.
    """

    missing_skills: tuple[str, ...]
    recommendations: tuple[str, ...]
    transferable_skills: tuple[str, ...]
    priority: tuple[tuple[str, str], ...]  # (skill, "high"|"medium"|"low")

    _VALID_PRIORITY_LEVELS: frozenset[str] = frozenset({"high", "medium", "low"})

    def __post_init__(self) -> None:
        """Validate priority levels."""
        for skill, level in self.priority:
            if level not in self._VALID_PRIORITY_LEVELS:
                raise ValidationError(
                    f"GapReport priority for '{skill}' must be "
                    f"'high', 'medium', or 'low', got '{level}'"
                )

    def high_priority_skills(self) -> tuple[str, ...]:
        """Return skills marked as high priority."""
        return tuple(skill for skill, level in self.priority if level == "high")
