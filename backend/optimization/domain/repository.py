"""IOptimizationRepository — abstract interface for session persistence.

Defined in the domain layer; implemented in the infrastructure layer.
All methods enforce tenant_id scoping for multi-tenant isolation.
"""

import uuid
from abc import ABC, abstractmethod

from optimization.domain.entities import OptimizationSession


class IOptimizationRepository(ABC):
    """Abstract repository for ``OptimizationSession`` aggregates.

    Implementations MUST scope every query by ``tenant_id`` to
    guarantee multi-tenant data isolation.
    """

    @abstractmethod
    async def save(self, session: OptimizationSession) -> None:
        """Persist a session aggregate (insert or update).

        Args:
            session: The aggregate to persist.
        """
        ...

    @abstractmethod
    async def find_by_id(
        self,
        session_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> OptimizationSession | None:
        """Look up a session by its ID, scoped to a tenant.

        Args:
            session_id: Session UUID.
            tenant_id: Tenant UUID for isolation.

        Returns:
            The session if found within the tenant, else ``None``.
        """
        ...

    @abstractmethod
    async def find_by_resume_id(
        self,
        resume_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[OptimizationSession]:
        """Return all sessions for a given resume within a tenant.

        Args:
            resume_id: Resume UUID to filter by.
            tenant_id: Tenant UUID for isolation.

        Returns:
            Possibly-empty list of sessions.
        """
        ...

    @abstractmethod
    async def find_by_user_id(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[OptimizationSession]:
        """Return all sessions for a given user within a tenant.

        Args:
            user_id: User UUID to filter by.
            tenant_id: Tenant UUID for isolation.

        Returns:
            Possibly-empty list of sessions.
        """
        ...
