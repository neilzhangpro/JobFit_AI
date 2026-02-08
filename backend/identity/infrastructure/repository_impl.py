"""UserRepository and TenantRepository — SQLAlchemy implementations.

Repository implementations provide data access using SQLAlchemy.
Must enforce tenant isolation on all queries.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities import Tenant, User
from identity.domain.repository import ITenantRepository, IUserRepository
from identity.domain.value_objects import Email, Role
from identity.infrastructure.models import TenantModel, UserModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of user data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_email(self, email: str, tenant_id: uuid.UUID) -> User | None:
        """Find user by email within a specific tenant."""
        stmt = select(UserModel).where(
            UserModel.email == email.lower().strip(),
            UserModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_email_any_tenant(self, email: str) -> User | None:
        """Find user by email across all tenants (for login)."""
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, user: User) -> User:
        """Persist a user (insert or update)."""
        model = self._to_model(user)
        self._session.add(model)
        await self._session.flush()
        return user

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        user = User(
            tenant_id=model.tenant_id,
            email=Email(model.email),
            hashed_password=model.hashed_password,
            role=Role(model.role),
            status=model.status,
        )
        user.id = model.id
        user.created_at = model.created_at
        user.updated_at = model.updated_at
        return user

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        """Convert domain entity to ORM model."""
        return UserModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            email=entity.email.value,
            hashed_password=entity.hashed_password,
            role=entity.role.value,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TenantRepository(ITenantRepository):
    """SQLAlchemy implementation of tenant data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Find tenant by ID."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_name(self, name: str) -> Tenant | None:
        """Find tenant by name."""
        stmt = select(TenantModel).where(TenantModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, tenant: Tenant) -> Tenant:
        """Persist a tenant (insert or update)."""
        model = self._to_model(tenant)
        self._session.add(model)
        await self._session.flush()
        return tenant

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: TenantModel) -> Tenant:
        """Convert ORM model to domain entity."""
        tenant = Tenant(
            name=model.name,
            plan=model.plan,
            status=model.status,
        )
        tenant.id = model.id
        tenant.created_at = model.created_at
        tenant.updated_at = model.updated_at
        return tenant

    @staticmethod
    def _to_model(entity: Tenant) -> TenantModel:
        """Convert domain entity to ORM model."""
        return TenantModel(
            id=entity.id,
            name=entity.name,
            plan=entity.plan,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
