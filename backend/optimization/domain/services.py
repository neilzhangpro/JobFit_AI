"""OptimizationDomainService — stateless business rules for scoring and transitions.

All methods are pure functions (no side effects, no I/O).
"""

from optimization.domain.value_objects import (
    ATSScore,
    ScoreBreakdown,
    SessionStatus,
)
from shared.domain.exceptions import ValidationError


class OptimizationDomainService:
    """Domain service for optimization business rules.

    Contains logic that doesn't belong to a single entity/value-object,
    such as cross-field validation and scoring policy decisions.
    """

    # ATS scoring weights (must match architecture doc §3.5)
    WEIGHT_KEYWORDS: float = 0.35
    WEIGHT_SKILLS: float = 0.30
    WEIGHT_EXPERIENCE: float = 0.25
    WEIGHT_FORMATTING: float = 0.10

    DEFAULT_THRESHOLD: float = 0.75
    DEFAULT_MAX_ATTEMPTS: int = 2

    # ----------------------------------------------------------
    # Validation helpers
    # ----------------------------------------------------------

    @staticmethod
    def validate_score(score: float, field_name: str = "score") -> None:
        """Ensure *score* is a number in [0.0, 1.0].

        Args:
            score: Value to validate.
            field_name: Label for error messages.

        Raises:
            ValidationError: If the value is out of range.
        """
        if not isinstance(score, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        if not 0.0 <= score <= 1.0:
            raise ValidationError(
                f"{field_name} must be between 0.0 and 1.0, got {score}"
            )

    @staticmethod
    def validate_status_transition(
        current: SessionStatus,
        target: SessionStatus,
    ) -> None:
        """Raise if the transition from *current* → *target* is not allowed.

        Args:
            current: Current session status.
            target: Desired next status.

        Raises:
            ValidationError: If the transition is invalid.
        """
        if not current.can_transition_to(target):
            raise ValidationError(
                f"Invalid status transition: {current.value} → {target.value}"
            )

    # ----------------------------------------------------------
    # Scoring
    # ----------------------------------------------------------

    @classmethod
    def calculate_overall_score(cls, breakdown: ScoreBreakdown) -> float:
        """Calculate the weighted overall ATS score.

        Uses the standard weighting defined in architecture doc §3.5:
        keywords=0.35, skills=0.30, experience=0.25, formatting=0.10.

        Args:
            breakdown: Per-category scores.

        Returns:
            Weighted overall score in [0.0, 1.0], rounded to 4 decimal places.
        """
        return round(breakdown.weighted_overall(), 4)

    @classmethod
    def create_ats_score(cls, breakdown: ScoreBreakdown) -> ATSScore:
        """Build an ``ATSScore`` value object with a calculated overall.

        Args:
            breakdown: Per-category scores.

        Returns:
            ``ATSScore`` with the weighted overall score.
        """
        overall = cls.calculate_overall_score(breakdown)
        return ATSScore(overall=overall, breakdown=breakdown)

    # ----------------------------------------------------------
    # Retry policy (mirrors architecture doc §4.2 / §4.6)
    # ----------------------------------------------------------

    @staticmethod
    def should_retry_rewrite(
        ats_score: float,
        rewrite_attempts: int,
        threshold: float = 0.75,
        max_attempts: int = 2,
    ) -> bool:
        """Decide whether the rewrite loop should retry.

        Decision logic:
            - score >= threshold → **no retry**
            - score < threshold AND attempts < max → **retry**
            - score < threshold AND attempts >= max → **no retry** (exhausted)

        Args:
            ats_score: Current ATS overall score in [0.0, 1.0].
            rewrite_attempts: Attempts completed so far.
            threshold: Minimum acceptable score.
            max_attempts: Maximum allowed retries.

        Returns:
            ``True`` if a retry should be performed.
        """
        if ats_score >= threshold:
            return False
        return rewrite_attempts < max_attempts
