"""IResumeRepository interface (ABC).

Repository interface defines the contract for resume data access.
Implementations live in the infrastructure layer.
"""

import uuid
from abc import ABC, abstractmethod

from resume.domain.entities import Resume


class IResumeRepository(ABC):
    """Abstract repository for Resume persistence.

    All implementations must enforce tenant isolation on queries.
    """

    @abstractmethod
    async def find_by_id(
        self, resume_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Resume | None:
        """Find a resume by ID within a specific tenant."""
        ...

    @abstractmethod
    async def find_by_user(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[Resume]:
        """Find all resumes for a user within a tenant."""
        ...

    @abstractmethod
    async def save(self, resume: Resume) -> Resume:
        """Persist a new or updated resume with its sections."""
        ...

    @abstractmethod
    async def delete(self, resume_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        """Delete a resume and its sections by ID."""
        ...
