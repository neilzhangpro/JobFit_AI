"""BillingApplicationService — manage subscriptions, query usage.

Orchestrates billing use cases by coordinating domain services
and repositories.  Contains no business rules itself.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from billing.domain.entities import Subscription, UsageRecord
from billing.domain.factories import SubscriptionFactory
from billing.domain.repository import ISubscriptionRepository, IUsageRepository
from billing.domain.services import QuotaEnforcementService
from billing.domain.value_objects import Plan
from shared.application.unit_of_work import IUnitOfWork
from shared.domain.exceptions import EntityNotFoundError


class BillingApplicationService:
    """Orchestrates subscription management and quota checks."""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        usage_repo: IUsageRepository,
        quota_service: QuotaEnforcementService,
        uow: IUnitOfWork,
    ) -> None:
        self._subscription_repo = subscription_repo
        self._usage_repo = usage_repo
        self._quota_service = quota_service
        self._uow = uow

    async def get_active_subscription(
        self, tenant_id: uuid.UUID
    ) -> Subscription | None:
        """Return the active subscription for a tenant, or None.

        Args:
            tenant_id: The tenant UUID.

        Returns:
            The active Subscription, or None if none exists.
        """
        return await self._subscription_repo.find_active_by_tenant_id(tenant_id)

    async def create_subscription(
        self,
        tenant_id: uuid.UUID,
        plan: Plan,
        stripe_subscription_id: str | None = None,
    ) -> Subscription:
        """Create a new subscription for a tenant.

        Args:
            tenant_id: The tenant UUID.
            plan: The plan tier.
            stripe_subscription_id: Optional Stripe ID.

        Returns:
            The persisted Subscription.
        """
        subscription = SubscriptionFactory.create_subscription(
            tenant_id=tenant_id,
            plan=plan,
            stripe_subscription_id=stripe_subscription_id,
        )
        await self._subscription_repo.save(subscription)
        await self._uow.commit()
        return subscription

    async def get_usage_summary(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Return total usage for a resource type within a period.

        Args:
            tenant_id: The tenant UUID.
            resource_type: E.g. "optimization" or "tokens".
            period_start: Start of the billing period (inclusive).
            period_end: End of the billing period (exclusive).

        Returns:
            The sum of consumed quantities.
        """
        return await self._usage_repo.get_usage_summary(
            tenant_id=tenant_id,
            resource_type=resource_type,
            period_start=period_start,
            period_end=period_end,
        )

    async def check_and_record_optimization(self, tenant_id: uuid.UUID) -> None:
        """Verify quota then record one optimization usage.

        Args:
            tenant_id: The tenant UUID.

        Raises:
            EntityNotFoundError: If no active subscription exists.
            QuotaExceededError: If the optimization limit is reached.
        """
        subscription = await self._subscription_repo.find_active_by_tenant_id(tenant_id)
        if subscription is None:
            raise EntityNotFoundError("No active subscription for this tenant")

        current_usage = await self._usage_repo.get_usage_summary(
            tenant_id=tenant_id,
            resource_type="optimization",
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
        )

        self._quota_service.check_optimization_quota(subscription, current_usage)

        record = UsageRecord(
            tenant_id=tenant_id,
            resource_type="optimization",
            quantity=1,
            recorded_at=datetime.utcnow(),
        )
        await self._usage_repo.save(record)
        await self._uow.commit()
