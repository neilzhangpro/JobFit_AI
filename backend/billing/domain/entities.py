"""Subscription (Aggregate Root) — one active per tenant. UsageRecord (Entity).

This module contains:
- Subscription: Aggregate root representing a tenant's subscription plan
  (one active subscription per tenant)
- UsageRecord: Entity representing usage of resources (optimizations, tokens)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from billing.domain.value_objects import Plan
from shared.domain.aggregate_root import AggregateRoot
from shared.domain.base_entity import BaseEntity
from shared.domain.domain_event import DomainEvent
from shared.domain.exceptions import ValidationError

# Valid subscription statuses
_VALID_STATUSES = {"active", "cancelled", "expired"}


class Subscription(AggregateRoot):
    """Subscription aggregate root — one active subscription per tenant.

    Manages lifecycle transitions (active → cancelled, active → expired)
    and publishes domain events on state changes.

    Args:
        tenant_id: UUID of the owning tenant.
        plan: The subscription plan tier.
        status: Current status (active, cancelled, expired).
        current_period_start: Start of the current billing period.
        current_period_end: End of the current billing period.
        stripe_subscription_id: Optional external Stripe subscription ID.

    Raises:
        ValidationError: If the initial status is not valid.
    """

    def __init__(
        self,
        tenant_id: uuid.UUID,
        plan: Plan,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        stripe_subscription_id: str | None = None,
    ) -> None:
        super().__init__()
        if status not in _VALID_STATUSES:
            raise ValidationError(
                f"Invalid subscription status: '{status}'. "
                f"Must be one of: {', '.join(sorted(_VALID_STATUSES))}"
            )
        self.tenant_id = tenant_id
        self.plan = plan
        self.status = status
        self.current_period_start = current_period_start
        self.current_period_end = current_period_end
        self.stripe_subscription_id = stripe_subscription_id

    def cancel(self) -> None:
        """Transition subscription from active to cancelled.

        Raises:
            ValidationError: If the subscription is not active.
        """
        if self.status != "active":
            raise ValidationError(
                f"Cannot cancel subscription with status '{self.status}'. "
                "Only active subscriptions can be cancelled."
            )
        self.status = "cancelled"
        self.updated_at = datetime.utcnow()
        self._add_event(
            DomainEvent(
                event_type="SubscriptionCancelled",
                payload={
                    "tenant_id": str(self.tenant_id),
                    "plan": self.plan.value,
                },
            )
        )

    def expire(self) -> None:
        """Transition subscription from active to expired.

        Raises:
            ValidationError: If the subscription is not active.
        """
        if self.status != "active":
            raise ValidationError(
                f"Cannot expire subscription with status '{self.status}'. "
                "Only active subscriptions can expire."
            )
        self.status = "expired"
        self.updated_at = datetime.utcnow()
        self._add_event(
            DomainEvent(
                event_type="SubscriptionExpired",
                payload={
                    "tenant_id": str(self.tenant_id),
                    "plan": self.plan.value,
                },
            )
        )


class UsageRecord(BaseEntity):
    """Usage record entity — tracks resource consumption per tenant.

    Each record represents a single usage event (e.g. one optimization
    run, a batch of token consumption).

    Args:
        tenant_id: UUID of the owning tenant.
        resource_type: Type of resource consumed (e.g. "optimization", "tokens").
        quantity: Amount consumed (must be >= 0).
        recorded_at: Timestamp of the usage event.

    Raises:
        ValidationError: If quantity is negative or resource_type is empty.
    """

    def __init__(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        quantity: int,
        recorded_at: datetime,
    ) -> None:
        super().__init__()
        if quantity < 0:
            raise ValidationError(f"quantity must be >= 0, got {quantity}")
        if not resource_type or not resource_type.strip():
            raise ValidationError("resource_type must not be empty")
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.quantity = quantity
        self.recorded_at = recorded_at
