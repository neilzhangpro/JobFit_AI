"""TenantFactory — creates Tenant aggregate with initial admin user.

Factories encapsulate complex object creation logic and ensure
all invariants are satisfied upon construction.
"""

from identity.domain.entities import Tenant, User
from identity.domain.services import PasswordHashingService
from identity.domain.value_objects import Email, Role
from shared.domain.domain_event import DomainEvent


class TenantFactory:
    """Factory for creating a Tenant with its first admin user."""

    @staticmethod
    def create_tenant_with_admin(
        name: str,
        admin_email: str,
        admin_password: str,
        hasher: PasswordHashingService,
    ) -> tuple[Tenant, User]:
        """Create a new tenant and its initial admin user.

        Args:
            name: Tenant organization name.
            admin_email: Email for the first admin user.
            admin_password: Plaintext password (will be hashed).
            hasher: Password hashing service.

        Returns:
            A tuple of (Tenant, User) with the admin user
            already added to the tenant.
        """
        tenant = Tenant(name=name)

        # Email VO validates format automatically
        email_vo = Email(admin_email)
        hashed = hasher.hash_password(admin_password)

        admin_user = User(
            tenant_id=tenant.id,
            email=email_vo,
            hashed_password=hashed,
            role=Role.TENANT_ADMIN,
        )

        tenant.add_user(admin_user)

        # Record domain event for cross-context communication
        tenant._add_event(
            DomainEvent(
                event_type="TenantCreated",
                payload={"tenant_id": str(tenant.id)},
            )
        )

        return tenant, admin_user
