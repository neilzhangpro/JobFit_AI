"""Tests for the Shared Kernel (DDD base classes and tenant context).

Covers: BaseEntity identity, BaseValueObject immutability, AggregateRoot
event collection, exception hierarchy, and TenantContext isolation.
"""

import dataclasses
import uuid

import pytest

from shared.domain.aggregate_root import AggregateRoot
from shared.domain.base_entity import BaseEntity
from shared.domain.base_value_object import BaseValueObject
from shared.domain.domain_event import DomainEvent
from shared.domain.exceptions import (
    AuthorizationError,
    DomainError,
    EntityNotFoundError,
    QuotaExceededError,
    ValidationError,
)
from shared.infrastructure.tenant_context import TenantContext


# ---------------------------------------------------------------------------
# Helper subclasses for testing (not part of production code)
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class _TestVO(BaseValueObject):
    """Concrete VO for testing equality and immutability."""

    value: str


# ---------------------------------------------------------------------------
# BaseEntity tests
# ---------------------------------------------------------------------------
class TestBaseEntity:
    """Tests for BaseEntity identity and equality."""

    def test_equality_by_id(self) -> None:
        """Two entities with the same id should be equal."""
        entity_a = BaseEntity()
        entity_b = BaseEntity()
        # Force same id
        entity_b.id = entity_a.id
        assert entity_a == entity_b

    def test_inequality_by_id(self) -> None:
        """Two entities with different ids should not be equal."""
        entity_a = BaseEntity()
        entity_b = BaseEntity()
        assert entity_a != entity_b


# ---------------------------------------------------------------------------
# BaseValueObject tests
# ---------------------------------------------------------------------------
class TestBaseValueObject:
    """Tests for BaseValueObject equality and immutability."""

    def test_equality_by_value(self) -> None:
        """Two VOs with the same field values should be equal."""
        vo_a = _TestVO(value="hello")
        vo_b = _TestVO(value="hello")
        assert vo_a == vo_b

    def test_immutability(self) -> None:
        """Modifying a frozen VO should raise FrozenInstanceError."""
        vo = _TestVO(value="hello")
        with pytest.raises(dataclasses.FrozenInstanceError):
            vo.value = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AggregateRoot tests
# ---------------------------------------------------------------------------
class TestAggregateRoot:
    """Tests for AggregateRoot domain event collection."""

    def test_collects_events(self) -> None:
        """Events added via _add_event should be returned by collect_events."""
        root = AggregateRoot()
        event = DomainEvent(event_type="TestEvent", payload={"key": "val"})
        root._add_event(event)

        collected = root.collect_events()
        assert len(collected) == 1
        assert collected[0].event_type == "TestEvent"
        assert collected[0].payload == {"key": "val"}

    def test_clears_events_after_collect(self) -> None:
        """After collect_events, the internal event list should be empty."""
        root = AggregateRoot()
        root._add_event(DomainEvent(event_type="E1"))
        root._add_event(DomainEvent(event_type="E2"))

        first = root.collect_events()
        assert len(first) == 2

        second = root.collect_events()
        assert len(second) == 0


# ---------------------------------------------------------------------------
# Exception hierarchy tests
# ---------------------------------------------------------------------------
class TestExceptionHierarchy:
    """Tests for the domain exception class hierarchy."""

    def test_domain_error_is_base(self) -> None:
        """All domain exceptions should be subclasses of DomainError."""
        assert issubclass(ValidationError, DomainError)
        assert issubclass(EntityNotFoundError, DomainError)
        assert issubclass(AuthorizationError, DomainError)
        assert issubclass(QuotaExceededError, DomainError)


# ---------------------------------------------------------------------------
# TenantContext tests
# ---------------------------------------------------------------------------
class TestTenantContext:
    """Tests for ContextVar-based tenant isolation."""

    def test_set_and_get(self) -> None:
        """Setting a tenant_id should make it retrievable."""
        test_id = str(uuid.uuid4())
        TenantContext.set_current_tenant_id(test_id)
        assert TenantContext.get_current_tenant_id() == test_id
        # Clean up for other tests
        TenantContext.clear()

    def test_raises_when_not_set(self) -> None:
        """Getting tenant_id without setting it should raise."""
        TenantContext.clear()
        with pytest.raises(AuthorizationError):
            TenantContext.get_current_tenant_id()
