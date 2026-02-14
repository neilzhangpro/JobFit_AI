"""Tests for the Billing bounded context (Person B: Platform).

Covers: Plan enum values, Quota value object immutability and validation,
Subscription aggregate root lifecycle, UsageRecord entity, SubscriptionFactory,
and zero-framework-import verification for the domain layer.
"""

import types
import uuid
from datetime import datetime, timedelta

import pytest

from billing.domain.entities import Subscription, UsageRecord
from billing.domain.factories import SubscriptionFactory
from billing.domain.value_objects import Plan, Quota, get_quota_for_plan
from shared.domain.exceptions import ValidationError


# ===================================================================
# Value Object Tests — Plan Enum
# ===================================================================
class TestPlan:
    """Tests for the Plan enum value object."""

    def test_plan_has_free(self) -> None:
        """Plan enum should include FREE."""
        assert Plan.FREE.value == "free"

    def test_plan_has_pro(self) -> None:
        """Plan enum should include PRO."""
        assert Plan.PRO.value == "pro"

    def test_plan_has_enterprise(self) -> None:
        """Plan enum should include ENTERPRISE."""
        assert Plan.ENTERPRISE.value == "enterprise"

    def test_plan_has_exactly_three_values(self) -> None:
        """Plan enum should have exactly 3 members."""
        assert len(Plan) == 3

    def test_plan_string_representation(self) -> None:
        """Plan values should be lowercase strings."""
        for plan in Plan:
            assert plan.value == plan.value.lower()


# ===================================================================
# Value Object Tests — Quota
# ===================================================================
class TestQuota:
    """Tests for the Quota value object."""

    def test_quota_creation(self) -> None:
        """Quota should store max_optimizations and max_tokens."""
        quota = Quota(max_optimizations=10, max_tokens=100_000)
        assert quota.max_optimizations == 10
        assert quota.max_tokens == 100_000

    def test_quota_immutability(self) -> None:
        """Quota should be immutable (frozen dataclass)."""
        quota = Quota(max_optimizations=10, max_tokens=100_000)
        with pytest.raises(AttributeError):
            quota.max_optimizations = 20  # type: ignore[misc]

    def test_quota_equality(self) -> None:
        """Two Quota objects with the same values should be equal."""
        q1 = Quota(max_optimizations=10, max_tokens=100_000)
        q2 = Quota(max_optimizations=10, max_tokens=100_000)
        assert q1 == q2

    def test_quota_inequality(self) -> None:
        """Two Quota objects with different values should not be equal."""
        q1 = Quota(max_optimizations=10, max_tokens=100_000)
        q2 = Quota(max_optimizations=20, max_tokens=100_000)
        assert q1 != q2

    def test_quota_negative_optimizations_raises(self) -> None:
        """Negative max_optimizations should raise ValidationError."""
        with pytest.raises(ValidationError):
            Quota(max_optimizations=-1, max_tokens=100_000)

    def test_quota_negative_tokens_raises(self) -> None:
        """Negative max_tokens should raise ValidationError."""
        with pytest.raises(ValidationError):
            Quota(max_optimizations=10, max_tokens=-1)

    def test_quota_zero_values_allowed(self) -> None:
        """Zero values should be valid (e.g., expired plan)."""
        quota = Quota(max_optimizations=0, max_tokens=0)
        assert quota.max_optimizations == 0
        assert quota.max_tokens == 0


# ===================================================================
# Value Object Tests — Plan-to-Quota Mapping
# ===================================================================
class TestPlanToQuotaMapping:
    """Tests for the get_quota_for_plan mapping function."""

    def test_free_plan_quota(self) -> None:
        """FREE plan should have limited quotas."""
        quota = get_quota_for_plan(Plan.FREE)
        assert isinstance(quota, Quota)
        assert quota.max_optimizations > 0
        assert quota.max_tokens > 0

    def test_pro_plan_quota_higher_than_free(self) -> None:
        """PRO plan quotas should exceed FREE plan."""
        free_quota = get_quota_for_plan(Plan.FREE)
        pro_quota = get_quota_for_plan(Plan.PRO)
        assert pro_quota.max_optimizations > free_quota.max_optimizations
        assert pro_quota.max_tokens > free_quota.max_tokens

    def test_enterprise_plan_quota_highest(self) -> None:
        """ENTERPRISE plan should have the highest quotas."""
        pro_quota = get_quota_for_plan(Plan.PRO)
        ent_quota = get_quota_for_plan(Plan.ENTERPRISE)
        assert ent_quota.max_optimizations > pro_quota.max_optimizations
        assert ent_quota.max_tokens > pro_quota.max_tokens


# ===================================================================
# Entity Tests — Subscription (Aggregate Root)
# ===================================================================
class TestSubscription:
    """Tests for the Subscription aggregate root."""

    def _make_subscription(
        self,
        plan: Plan = Plan.FREE,
        status: str = "active",
    ) -> Subscription:
        """Helper to create a Subscription for testing."""
        now = datetime.utcnow()
        return Subscription(
            tenant_id=uuid.uuid4(),
            plan=plan,
            status=status,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

    def test_subscription_creation(self) -> None:
        """Subscription should be created with correct attributes."""
        tenant_id = uuid.uuid4()
        now = datetime.utcnow()
        sub = Subscription(
            tenant_id=tenant_id,
            plan=Plan.PRO,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        assert sub.tenant_id == tenant_id
        assert sub.plan == Plan.PRO
        assert sub.status == "active"
        assert sub.current_period_start == now
        assert sub.current_period_end == now + timedelta(days=30)
        assert sub.stripe_subscription_id is None

    def test_subscription_has_uuid(self) -> None:
        """Subscription should have a UUID id from BaseEntity."""
        sub = self._make_subscription()
        assert isinstance(sub.id, uuid.UUID)

    def test_subscription_has_timestamps(self) -> None:
        """Subscription should have created_at timestamp."""
        sub = self._make_subscription()
        assert isinstance(sub.created_at, datetime)

    def test_cancel_active_subscription(self) -> None:
        """An active subscription should transition to cancelled."""
        sub = self._make_subscription(status="active")
        sub.cancel()
        assert sub.status == "cancelled"

    def test_expire_active_subscription(self) -> None:
        """An active subscription should transition to expired."""
        sub = self._make_subscription(status="active")
        sub.expire()
        assert sub.status == "expired"

    def test_cancel_already_cancelled_raises(self) -> None:
        """Cancelling an already cancelled subscription should raise."""
        sub = self._make_subscription(status="active")
        sub.cancel()
        with pytest.raises(ValidationError):
            sub.cancel()

    def test_cancel_expired_raises(self) -> None:
        """Cancelling an expired subscription should raise."""
        sub = self._make_subscription(status="active")
        sub.expire()
        with pytest.raises(ValidationError):
            sub.cancel()

    def test_expire_cancelled_raises(self) -> None:
        """Expiring a cancelled subscription should raise."""
        sub = self._make_subscription(status="active")
        sub.cancel()
        with pytest.raises(ValidationError):
            sub.expire()

    def test_subscription_invalid_status_raises(self) -> None:
        """Creating a subscription with invalid status should raise."""
        with pytest.raises(ValidationError):
            Subscription(
                tenant_id=uuid.uuid4(),
                plan=Plan.FREE,
                status="invalid_status",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
            )

    def test_subscription_is_aggregate_root(self) -> None:
        """Subscription should support domain events (AggregateRoot)."""
        sub = self._make_subscription()
        events = sub.collect_events()
        assert isinstance(events, list)

    def test_cancel_publishes_domain_event(self) -> None:
        """Cancelling subscription should publish a domain event."""
        sub = self._make_subscription(status="active")
        sub.cancel()
        events = sub.collect_events()
        assert len(events) >= 1
        assert events[0].event_type == "SubscriptionCancelled"

    def test_subscription_with_stripe_id(self) -> None:
        """Subscription should accept optional stripe_subscription_id."""
        now = datetime.utcnow()
        sub = Subscription(
            tenant_id=uuid.uuid4(),
            plan=Plan.PRO,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            stripe_subscription_id="sub_abc123",
        )
        assert sub.stripe_subscription_id == "sub_abc123"


# ===================================================================
# Entity Tests — UsageRecord
# ===================================================================
class TestUsageRecord:
    """Tests for the UsageRecord entity."""

    def test_usage_record_creation(self) -> None:
        """UsageRecord should store all attributes correctly."""
        tenant_id = uuid.uuid4()
        now = datetime.utcnow()
        record = UsageRecord(
            tenant_id=tenant_id,
            resource_type="optimization",
            quantity=1,
            recorded_at=now,
        )
        assert record.tenant_id == tenant_id
        assert record.resource_type == "optimization"
        assert record.quantity == 1
        assert record.recorded_at == now

    def test_usage_record_has_uuid(self) -> None:
        """UsageRecord should have a UUID id from BaseEntity."""
        record = UsageRecord(
            tenant_id=uuid.uuid4(),
            resource_type="tokens",
            quantity=5000,
            recorded_at=datetime.utcnow(),
        )
        assert isinstance(record.id, uuid.UUID)

    def test_usage_record_negative_quantity_raises(self) -> None:
        """Negative quantity should raise ValidationError."""
        with pytest.raises(ValidationError):
            UsageRecord(
                tenant_id=uuid.uuid4(),
                resource_type="optimization",
                quantity=-1,
                recorded_at=datetime.utcnow(),
            )

    def test_usage_record_zero_quantity_allowed(self) -> None:
        """Zero quantity should be valid (e.g., no-op record)."""
        record = UsageRecord(
            tenant_id=uuid.uuid4(),
            resource_type="optimization",
            quantity=0,
            recorded_at=datetime.utcnow(),
        )
        assert record.quantity == 0

    def test_usage_record_empty_resource_type_raises(self) -> None:
        """Empty resource_type should raise ValidationError."""
        with pytest.raises(ValidationError):
            UsageRecord(
                tenant_id=uuid.uuid4(),
                resource_type="",
                quantity=1,
                recorded_at=datetime.utcnow(),
            )


# ===================================================================
# Factory Tests — SubscriptionFactory
# ===================================================================
class TestSubscriptionFactory:
    """Tests for SubscriptionFactory."""

    def test_create_free_subscription(self) -> None:
        """Factory should create a FREE plan subscription."""
        tenant_id = uuid.uuid4()
        sub = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id,
            plan=Plan.FREE,
        )
        assert isinstance(sub, Subscription)
        assert sub.tenant_id == tenant_id
        assert sub.plan == Plan.FREE
        assert sub.status == "active"

    def test_create_pro_subscription(self) -> None:
        """Factory should create a PRO plan subscription."""
        tenant_id = uuid.uuid4()
        sub = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id,
            plan=Plan.PRO,
        )
        assert sub.plan == Plan.PRO
        assert sub.status == "active"

    def test_create_enterprise_subscription(self) -> None:
        """Factory should create an ENTERPRISE plan subscription."""
        tenant_id = uuid.uuid4()
        sub = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id,
            plan=Plan.ENTERPRISE,
        )
        assert sub.plan == Plan.ENTERPRISE
        assert sub.status == "active"

    def test_factory_sets_period_dates(self) -> None:
        """Factory should set current_period_start and current_period_end."""
        sub = SubscriptionFactory.create_subscription(
            tenant_id=uuid.uuid4(),
            plan=Plan.FREE,
        )
        assert sub.current_period_start is not None
        assert sub.current_period_end is not None
        # Period should be approximately 30 days
        delta = sub.current_period_end - sub.current_period_start
        assert 29 <= delta.days <= 31

    def test_factory_publishes_subscription_created_event(self) -> None:
        """Factory should publish SubscriptionCreated domain event."""
        sub = SubscriptionFactory.create_subscription(
            tenant_id=uuid.uuid4(),
            plan=Plan.FREE,
        )
        events = sub.collect_events()
        assert len(events) >= 1
        assert events[0].event_type == "SubscriptionCreated"


# ===================================================================
# Domain Layer Purity — Zero Framework Imports
# ===================================================================
class TestDomainLayerPurity:
    """Verify that billing domain layer has zero external framework imports."""

    def test_no_sqlalchemy_in_value_objects(self) -> None:
        """value_objects.py should not import SQLAlchemy."""
        import billing.domain.value_objects as mod

        source = _get_module_source(mod)
        assert "sqlalchemy" not in source.lower()

    def test_no_sqlalchemy_in_entities(self) -> None:
        """entities.py should not import SQLAlchemy."""
        import billing.domain.entities as mod

        source = _get_module_source(mod)
        assert "sqlalchemy" not in source.lower()

    def test_no_sqlalchemy_in_factories(self) -> None:
        """factories.py should not import SQLAlchemy."""
        import billing.domain.factories as mod

        source = _get_module_source(mod)
        assert "sqlalchemy" not in source.lower()

    def test_no_fastapi_in_domain(self) -> None:
        """Domain layer should not import FastAPI."""
        import billing.domain.entities as entities_mod
        import billing.domain.factories as factories_mod
        import billing.domain.value_objects as vo_mod

        for mod in [vo_mod, entities_mod, factories_mod]:
            source = _get_module_source(mod)
            assert "fastapi" not in source.lower()

    def test_no_pydantic_in_domain(self) -> None:
        """Domain layer should not import Pydantic (use dataclasses)."""
        import billing.domain.entities as entities_mod
        import billing.domain.factories as factories_mod
        import billing.domain.value_objects as vo_mod

        for mod in [vo_mod, entities_mod, factories_mod]:
            source = _get_module_source(mod)
            assert "pydantic" not in source.lower()


def _get_module_source(module: types.ModuleType) -> str:
    """Read the source code of a Python module file."""
    import inspect

    return inspect.getsource(module)
