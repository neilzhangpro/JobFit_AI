"""Domain entities for optimization.

OptimizationSession (Aggregate Root) — lifecycle of a single optimization
request with enforced status transitions and domain event publishing.

OptimizationResult (Entity) — immutable record of pipeline outputs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from optimization.domain.value_objects import (
    ATSScore,
    GapReport,
    JDAnalysis,
    SessionStatus,
)
from shared.domain.aggregate_root import AggregateRoot
from shared.domain.base_entity import BaseEntity
from shared.domain.domain_event import DomainEvent
from shared.domain.exceptions import ValidationError

# Minimum JD length to prevent trivially short / empty submissions
_MIN_JD_LENGTH = 50


class OptimizationSession(AggregateRoot):
    """Aggregate root tracking a resume-optimization lifecycle.

    Business invariants:
        - Transitions follow PENDING → PROCESSING → COMPLETED | FAILED.
        - Terminal sessions (COMPLETED / FAILED) cannot be modified.
        - ``tenant_id`` is set once at creation and never changed.
    """

    def __init__(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        jd_text: str,
    ) -> None:
        """Create a new optimization session in PENDING status.

        Args:
            tenant_id: Owning tenant (multi-tenant isolation).
            user_id: User who initiated the optimization.
            resume_id: Resume being optimized.
            jd_text: Raw job-description text.

        Raises:
            ValidationError: If *jd_text* is shorter than 50 characters.
        """
        super().__init__()
        if not jd_text or len(jd_text.strip()) < _MIN_JD_LENGTH:
            raise ValidationError(
                f"Job description text must be at least {_MIN_JD_LENGTH} characters"
            )

        self.tenant_id = tenant_id
        self.user_id = user_id
        self.resume_id = resume_id
        self.jd_text = jd_text
        self.status = SessionStatus.PENDING
        self.result: OptimizationResult | None = None
        self.error_message: str | None = None

    # ----------------------------------------------------------
    # Status transition methods
    # ----------------------------------------------------------

    def start_processing(self) -> None:
        """Move session to PROCESSING.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        self._transition_to(SessionStatus.PROCESSING)
        self._add_event(DomainEvent(
            event_type="optimization.session.processing_started",
            payload={
                "session_id": str(self.id),
                "tenant_id": str(self.tenant_id),
                "user_id": str(self.user_id),
                "resume_id": str(self.resume_id),
            },
        ))

    def complete(self, result: OptimizationResult) -> None:
        """Move session to COMPLETED and attach the pipeline result.

        Args:
            result: Finalized optimization output.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        self._transition_to(SessionStatus.COMPLETED)
        self.result = result
        self._add_event(DomainEvent(
            event_type="optimization.session.completed",
            payload={
                "session_id": str(self.id),
                "tenant_id": str(self.tenant_id),
                "user_id": str(self.user_id),
                "ats_score": result.ats_score.overall if result.ats_score else 0.0,
                "total_tokens_used": result.total_tokens_used,
            },
        ))

    def fail(self, error_message: str) -> None:
        """Move session to FAILED.

        Args:
            error_message: Human-readable reason for failure.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        self._transition_to(SessionStatus.FAILED)
        self.error_message = error_message
        self._add_event(DomainEvent(
            event_type="optimization.session.failed",
            payload={
                "session_id": str(self.id),
                "tenant_id": str(self.tenant_id),
                "error_message": error_message,
            },
        ))

    # ----------------------------------------------------------
    # Queries
    # ----------------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        """True when the session is in COMPLETED or FAILED state."""
        return self.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}

    # ----------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------

    def _transition_to(self, target: SessionStatus) -> None:
        """Validate and execute a status transition.

        Args:
            target: Desired next status.

        Raises:
            ValidationError: If the transition violates the state machine.
        """
        if not self.status.can_transition_to(target):
            raise ValidationError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target
        self.updated_at = datetime.utcnow()


class OptimizationResult(BaseEntity):
    """Immutable record of a completed optimization pipeline run.

    Holds JD analysis, rewritten sections, ATS score, gap report,
    and token-usage metadata.  Created once by the application layer
    and attached to the parent ``OptimizationSession``.
    """

    def __init__(
        self,
        session_id: uuid.UUID,
        tenant_id: uuid.UUID,
        jd_analysis: JDAnalysis | None = None,
        optimized_sections: dict[str, list[str]] | None = None,
        ats_score: ATSScore | None = None,
        gap_report: GapReport | None = None,
        rewrite_attempts: int = 0,
        total_tokens_used: int = 0,
    ) -> None:
        """Initialize an optimization result.

        Args:
            session_id: Parent session this result belongs to.
            tenant_id: Owning tenant (multi-tenant isolation).
            jd_analysis: Structured JD analysis from the pipeline.
            optimized_sections: Rewritten sections keyed by type
                (e.g. ``{"experience": [...], "skills_summary": [...]``).
            ats_score: ATS compatibility score and breakdown.
            gap_report: Missing-skills analysis and recommendations.
            rewrite_attempts: How many rewrite iterations ran.
            total_tokens_used: Total LLM tokens consumed.
        """
        super().__init__()
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.jd_analysis = jd_analysis
        self.optimized_sections: dict[str, list[str]] = optimized_sections or {}
        self.ats_score = ats_score
        self.gap_report = gap_report
        self.rewrite_attempts = rewrite_attempts
        self.total_tokens_used = total_tokens_used
