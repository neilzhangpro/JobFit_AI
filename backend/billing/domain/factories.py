"""SubscriptionFactory — creates subscriptions with plan-based defaults.

Factories encapsulate complex creation logic and ensure all
invariants are satisfied upon construction.
"""

import uuid
from datetime import datetime, timedelta

from billing.domain.entities import Subscription
from billing.domain.value_objects import Plan
from shared.domain.domain_event import DomainEvent

# Default billing period length (days)
_DEFAULT_PERIOD_DAYS = 30


class SubscriptionFactory:
    """Factory for creating Subscription aggregates with plan-based defaults.

    Handles setting the billing period, status, and publishing
    the SubscriptionCreated domain event on construction.
    """

    @staticmethod
    def create_subscription(
        tenant_id: uuid.UUID,
        plan: Plan,
        stripe_subscription_id: str | None = None,
    ) -> Subscription:
        """Create a new active Subscription with default period dates.

        Args:
            tenant_id: UUID of the owning tenant.
            plan: The subscription plan tier (FREE, PRO, ENTERPRISE).
            stripe_subscription_id: Optional external Stripe ID.

        Returns:
            A fully constructed active Subscription with a 30-day period.
        """
        now = datetime.utcnow()
        subscription = Subscription(
            tenant_id=tenant_id,
            plan=plan,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=_DEFAULT_PERIOD_DAYS),
            stripe_subscription_id=stripe_subscription_id,
        )

        # Record domain event for cross-context communication
        subscription._add_event(
            DomainEvent(
                event_type="SubscriptionCreated",
                payload={
                    "tenant_id": str(tenant_id),
                    "plan": plan.value,
                },
            )
        )

        return subscription
