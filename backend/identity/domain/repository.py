"""IUserRepository and ITenantRepository interfaces (ABC).

Repository interfaces define the contract for data access.
Implementations live in the infrastructure layer.
"""

import uuid
from abc import ABC, abstractmethod

from identity.domain.entities import Tenant, User


class IUserRepository(ABC):
    """Abstract repository for User persistence.

    All implementations must enforce tenant isolation on queries.
    """

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by ID within the current tenant scope."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: uuid.UUID) -> User | None:
        """Find a user by email within a specific tenant."""
        ...

    @abstractmethod
    async def find_by_email_any_tenant(self, email: str) -> User | None:
        """Find a user by email across all tenants.

        Used only during login when tenant context is not yet set.
        """
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a new or updated user."""
        ...


class ITenantRepository(ABC):
    """Abstract repository for Tenant persistence."""

    @abstractmethod
    async def find_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Find a tenant by ID."""
        ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Tenant | None:
        """Find a tenant by name."""
        ...

    @abstractmethod
    async def save(self, tenant: Tenant) -> Tenant:
        """Persist a new or updated tenant."""
        ...
