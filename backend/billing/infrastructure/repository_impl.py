"""SubscriptionRepository, UsageRepository — SQLAlchemy implementations.

All queries are scoped by tenant_id to enforce multi-tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from billing.domain.entities import Subscription, UsageRecord
from billing.domain.repository import ISubscriptionRepository, IUsageRepository
from billing.domain.value_objects import Plan
from billing.infrastructure.models import SubscriptionModel, UsageRecordModel


class SubscriptionRepository(ISubscriptionRepository):
    """SQLAlchemy implementation of subscription data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, subscription: Subscription) -> Subscription:
        """Persist a new or updated subscription."""
        model = self._to_model(subscription)
        merged = await self._session.merge(model)
        await self._session.flush()
        subscription.id = merged.id
        return subscription

    async def find_by_tenant_id(self, tenant_id: uuid.UUID) -> list[Subscription]:
        """Find all subscriptions for a tenant."""
        stmt = select(SubscriptionModel).where(SubscriptionModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def find_active_by_tenant_id(
        self, tenant_id: uuid.UUID
    ) -> Subscription | None:
        """Find the active subscription for a tenant."""
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.tenant_id == tenant_id,
            SubscriptionModel.status == "active",
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: SubscriptionModel) -> Subscription:
        """Convert ORM model to domain entity."""
        sub = Subscription(
            tenant_id=model.tenant_id,
            plan=Plan(model.plan),
            status=model.status,
            current_period_start=model.current_period_start,
            current_period_end=model.current_period_end,
            stripe_subscription_id=model.stripe_subscription_id,
        )
        sub.id = model.id
        sub.created_at = model.created_at
        sub.updated_at = model.updated_at
        return sub

    @staticmethod
    def _to_model(entity: Subscription) -> SubscriptionModel:
        """Convert domain entity to ORM model."""
        return SubscriptionModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            plan=entity.plan.value,
            status=entity.status,
            current_period_start=entity.current_period_start,
            current_period_end=entity.current_period_end,
            stripe_subscription_id=entity.stripe_subscription_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class UsageRepository(IUsageRepository):
    """SQLAlchemy implementation of usage record data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, usage_record: UsageRecord) -> UsageRecord:
        """Persist a new usage record."""
        model = self._to_model(usage_record)
        merged = await self._session.merge(model)
        await self._session.flush()
        usage_record.id = merged.id
        return usage_record

    async def find_by_tenant_and_period(
        self,
        tenant_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> list[UsageRecord]:
        """Find usage records for a tenant within a billing period."""
        stmt = select(UsageRecordModel).where(
            UsageRecordModel.tenant_id == tenant_id,
            UsageRecordModel.recorded_at >= period_start,
            UsageRecordModel.recorded_at < period_end,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_usage_summary(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Sum usage quantity for a resource type in a period."""
        stmt = select(func.coalesce(func.sum(UsageRecordModel.quantity), 0)).where(
            UsageRecordModel.tenant_id == tenant_id,
            UsageRecordModel.resource_type == resource_type,
            UsageRecordModel.recorded_at >= period_start,
            UsageRecordModel.recorded_at < period_end,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: UsageRecordModel) -> UsageRecord:
        """Convert ORM model to domain entity."""
        record = UsageRecord(
            tenant_id=model.tenant_id,
            resource_type=model.resource_type,
            quantity=model.quantity,
            recorded_at=model.recorded_at,
        )
        record.id = model.id
        record.created_at = model.created_at
        return record

    @staticmethod
    def _to_model(entity: UsageRecord) -> UsageRecordModel:
        """Convert domain entity to ORM model."""
        return UsageRecordModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            resource_type=entity.resource_type,
            quantity=entity.quantity,
            recorded_at=entity.recorded_at,
            created_at=entity.created_at,
        )
