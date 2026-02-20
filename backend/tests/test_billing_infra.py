"""Integration tests for billing infrastructure (repositories + ORM).

Covers SubscriptionRepository, UsageRepository, and mandatory
tenant isolation verification.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from billing.domain.entities import Subscription, UsageRecord
from billing.domain.factories import SubscriptionFactory
from billing.domain.value_objects import Plan
from billing.infrastructure.repository_impl import (
    SubscriptionRepository,
    UsageRepository,
)
from identity.infrastructure.models import TenantModel

# --- helpers ---


async def _seed_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Insert a minimal tenant row so FK constraints are satisfied.

    Uses merge to avoid duplicate-key errors when the same tenant
    is seeded across multiple tests sharing a file-based SQLite DB.
    """
    model = TenantModel(
        id=tenant_id,
        name=f"tenant-{tenant_id.hex[:8]}",
        plan="free",
        status="active",
    )
    await session.merge(model)
    await session.flush()


# ===================================================================
# SubscriptionRepository Tests
# ===================================================================
class TestSubscriptionRepository:
    """Integration tests for SubscriptionRepository."""

    @pytest.mark.asyncio
    async def test_save_and_find_by_tenant(self, db_session: AsyncSession) -> None:
        """Should persist and retrieve subscriptions for a tenant."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = SubscriptionRepository(db_session)
        sub = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id, plan=Plan.PRO
        )
        await repo.save(sub)
        await db_session.commit()

        results = await repo.find_by_tenant_id(tenant_id)
        assert len(results) == 1
        assert results[0].tenant_id == tenant_id
        assert results[0].plan == Plan.PRO
        assert results[0].status == "active"

    @pytest.mark.asyncio
    async def test_find_active_by_tenant(self, db_session: AsyncSession) -> None:
        """Should return only the active subscription."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = SubscriptionRepository(db_session)

        active = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id, plan=Plan.FREE
        )
        await repo.save(active)

        now = datetime.utcnow()
        cancelled = Subscription(
            tenant_id=tenant_id,
            plan=Plan.FREE,
            status="cancelled",
            current_period_start=now - timedelta(days=60),
            current_period_end=now - timedelta(days=30),
        )
        await repo.save(cancelled)
        await db_session.commit()

        result = await repo.find_active_by_tenant_id(tenant_id)
        assert result is not None
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_find_active_returns_none_when_absent(
        self, db_session: AsyncSession
    ) -> None:
        """Should return None when no active subscription exists."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = SubscriptionRepository(db_session)
        result = await repo.find_active_by_tenant_id(tenant_id)
        assert result is None


# ===================================================================
# UsageRepository Tests
# ===================================================================
class TestUsageRepository:
    """Integration tests for UsageRepository."""

    @pytest.mark.asyncio
    async def test_save_and_find_by_period(self, db_session: AsyncSession) -> None:
        """Should persist and retrieve usage records by period."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = UsageRepository(db_session)
        now = datetime.utcnow()
        record = UsageRecord(
            tenant_id=tenant_id,
            resource_type="optimization",
            quantity=1,
            recorded_at=now,
        )
        await repo.save(record)
        await db_session.commit()

        results = await repo.find_by_tenant_and_period(
            tenant_id=tenant_id,
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=1),
        )
        assert len(results) == 1
        assert results[0].resource_type == "optimization"
        assert results[0].quantity == 1

    @pytest.mark.asyncio
    async def test_get_usage_summary(self, db_session: AsyncSession) -> None:
        """Should sum quantities for a resource type in a period."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = UsageRepository(db_session)
        now = datetime.utcnow()
        period_start = now - timedelta(days=1)
        period_end = now + timedelta(days=1)

        for _ in range(3):
            r = UsageRecord(
                tenant_id=tenant_id,
                resource_type="optimization",
                quantity=1,
                recorded_at=now,
            )
            await repo.save(r)

        token_record = UsageRecord(
            tenant_id=tenant_id,
            resource_type="tokens",
            quantity=5000,
            recorded_at=now,
        )
        await repo.save(token_record)
        await db_session.commit()

        opt_total = await repo.get_usage_summary(
            tenant_id, "optimization", period_start, period_end
        )
        assert opt_total == 3

        tok_total = await repo.get_usage_summary(
            tenant_id, "tokens", period_start, period_end
        )
        assert tok_total == 5000

    @pytest.mark.asyncio
    async def test_get_usage_summary_returns_zero_when_empty(
        self, db_session: AsyncSession
    ) -> None:
        """Should return 0 when no records exist for the period."""
        tenant_id = uuid.uuid4()
        await _seed_tenant(db_session, tenant_id)

        repo = UsageRepository(db_session)
        now = datetime.utcnow()
        total = await repo.get_usage_summary(
            tenant_id,
            "optimization",
            now - timedelta(days=1),
            now + timedelta(days=1),
        )
        assert total == 0


# ===================================================================
# Tenant Isolation Test (MANDATORY)
# ===================================================================
class TestTenantIsolation:
    """Verify strict tenant isolation at the repository level."""

    @pytest.mark.asyncio
    @pytest.mark.tenant_isolation
    async def test_tenant_a_cannot_see_tenant_b_subscriptions(
        self, db_session: AsyncSession
    ) -> None:
        """Tenant A's subscriptions must be invisible to Tenant B."""
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _seed_tenant(db_session, tenant_a)
        await _seed_tenant(db_session, tenant_b)

        repo = SubscriptionRepository(db_session)

        sub_a = SubscriptionFactory.create_subscription(
            tenant_id=tenant_a, plan=Plan.ENTERPRISE
        )
        await repo.save(sub_a)
        await db_session.commit()

        result_b = await repo.find_by_tenant_id(tenant_b)
        assert len(result_b) == 0

        active_b = await repo.find_active_by_tenant_id(tenant_b)
        assert active_b is None

    @pytest.mark.asyncio
    @pytest.mark.tenant_isolation
    async def test_tenant_a_cannot_see_tenant_b_usage(
        self, db_session: AsyncSession
    ) -> None:
        """Tenant A's usage records must be invisible to Tenant B."""
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _seed_tenant(db_session, tenant_a)
        await _seed_tenant(db_session, tenant_b)

        repo = UsageRepository(db_session)
        now = datetime.utcnow()

        record = UsageRecord(
            tenant_id=tenant_a,
            resource_type="optimization",
            quantity=1,
            recorded_at=now,
        )
        await repo.save(record)
        await db_session.commit()

        total_b = await repo.get_usage_summary(
            tenant_b,
            "optimization",
            now - timedelta(days=1),
            now + timedelta(days=1),
        )
        assert total_b == 0
