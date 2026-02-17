"""OptimizationSessionFactory — creates session aggregates with validation.

Encapsulates creation logic so callers never construct
``OptimizationSession`` directly.
"""

import uuid

from optimization.domain.entities import OptimizationSession
from shared.domain.exceptions import ValidationError


class OptimizationSessionFactory:
    """Factory for ``OptimizationSession`` aggregate roots.

    Validates inputs and returns a properly initialized session
    in PENDING status.
    """

    @staticmethod
    def create_session(
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        jd_text: str,
    ) -> OptimizationSession:
        """Create a new optimization session.

        Args:
            tenant_id: Owning tenant.
            user_id: User initiating the optimization.
            resume_id: Resume to optimize.
            jd_text: Raw job-description text.

        Returns:
            A new ``OptimizationSession`` in PENDING status.

        Raises:
            ValidationError: If any required input is ``None``.
        """
        if tenant_id is None:
            raise ValidationError("tenant_id is required")
        if user_id is None:
            raise ValidationError("user_id is required")
        if resume_id is None:
            raise ValidationError("resume_id is required")

        # jd_text length validation is enforced inside OptimizationSession.__init__
        return OptimizationSession(
            tenant_id=tenant_id,
            user_id=user_id,
            resume_id=resume_id,
            jd_text=jd_text,
        )
