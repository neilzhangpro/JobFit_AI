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


# ---------------------------------------------------------------------------
# InProcessEventBus tests
# ---------------------------------------------------------------------------
class TestInProcessEventBus:
    """Tests for the in-process domain event bus."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish_delivers_event(self) -> None:
        """A subscribed handler should receive the published event."""
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("OrderPlaced", handler)

        event = DomainEvent(event_type="OrderPlaced", payload={"order_id": "1"})
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].event_type == "OrderPlaced"
        assert received[0].payload == {"order_id": "1"}

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_receive_event(self) -> None:
        """All handlers for the same event type should be invoked."""
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        calls: list[str] = []

        async def handler_a(event: DomainEvent) -> None:
            calls.append("a")

        async def handler_b(event: DomainEvent) -> None:
            calls.append("b")

        bus.subscribe("UserCreated", handler_a)
        bus.subscribe("UserCreated", handler_b)

        await bus.publish(DomainEvent(event_type="UserCreated"))

        assert sorted(calls) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_block_others(self) -> None:
        """A failing handler must not prevent other handlers from running."""
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        calls: list[str] = []

        async def failing_handler(event: DomainEvent) -> None:
            raise RuntimeError("boom")

        async def good_handler(event: DomainEvent) -> None:
            calls.append("ok")

        bus.subscribe("TestEvent", failing_handler)
        bus.subscribe("TestEvent", good_handler)

        await bus.publish(DomainEvent(event_type="TestEvent"))

        assert calls == ["ok"]

    @pytest.mark.asyncio
    async def test_unsubscribed_event_type_is_silently_ignored(self) -> None:
        """Publishing an event with no subscribers should not raise."""
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        await bus.publish(DomainEvent(event_type="NobodyListens"))

    @pytest.mark.asyncio
    async def test_different_event_types_are_isolated(self) -> None:
        """Handlers for one event type must not receive other types."""
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        received: list[str] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event.event_type)

        bus.subscribe("TypeA", handler)

        await bus.publish(DomainEvent(event_type="TypeB"))
        assert received == []

        await bus.publish(DomainEvent(event_type="TypeA"))
        assert received == ["TypeA"]

    def test_implements_ieventbus_interface(self) -> None:
        """InProcessEventBus should be an instance of IEventBus."""
        from shared.domain.domain_event import IEventBus
        from shared.infrastructure.event_bus_impl import InProcessEventBus

        bus = InProcessEventBus()
        assert isinstance(bus, IEventBus)
