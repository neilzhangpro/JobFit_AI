"""Tenant (Aggregate Root) and User (Entity) for the Identity context.

Tenant must have at least one admin user. User email is unique within tenant.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from identity.domain.value_objects import Email, Role
from shared.domain.aggregate_root import AggregateRoot
from shared.domain.base_entity import BaseEntity
from shared.domain.exceptions import ValidationError

if TYPE_CHECKING:
    from identity.domain.services import PasswordHashingService


class User(BaseEntity):
    """User entity — belongs to exactly one Tenant.

    Contains business behavior related to the user's own data
    (e.g. password verification). Created via TenantFactory.
    """

    def __init__(
        self,
        tenant_id: uuid.UUID,
        email: Email,
        hashed_password: str,
        role: Role,
        status: str = "active",
    ) -> None:
        super().__init__()
        self.tenant_id = tenant_id
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.status = status

    def verify_password(
        self,
        raw_password: str,
        hasher: PasswordHashingService,
    ) -> bool:
        """Verify a raw password against the stored hash.

        Args:
            raw_password: The plaintext password to check.
            hasher: A PasswordHashingService instance.

        Returns:
            True if the password matches, False otherwise.
        """
        return hasher.verify_password(raw_password, self.hashed_password)


class Tenant(AggregateRoot):
    """Tenant aggregate root — the organizational boundary.

    Enforces the invariant that email addresses are unique within
    the tenant, and that at least one admin user exists.
    """

    def __init__(
        self,
        name: str,
        plan: str = "free",
        status: str = "active",
    ) -> None:
        super().__init__()
        self.name = name
        self.plan = plan
        self.status = status
        self._users: list[User] = []

    def add_user(self, user: User) -> None:
        """Add a user to this tenant.

        Raises:
            ValidationError: If a user with the same email
                already exists in this tenant.
        """
        existing_emails = [u.email.value for u in self._users]
        if user.email.value in existing_emails:
            raise ValidationError(
                f"Email {user.email.value} already exists in tenant {self.name}"
            )
        self._users.append(user)

    @property
    def users(self) -> list[User]:
        """Return a copy of the internal user list."""
        return list(self._users)
