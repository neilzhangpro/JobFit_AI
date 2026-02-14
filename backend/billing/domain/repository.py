"""ISubscriptionRepository and IUsageRepository interfaces (ABC).

Repository interfaces define the contract for data access.
Implementations live in the infrastructure layer.
All methods must enforce tenant isolation via tenant_id scoping.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from billing.domain.entities import Subscription, UsageRecord


class ISubscriptionRepository(ABC):
    """Abstract repository for Subscription persistence.

    All implementations must enforce tenant isolation on queries.
    """

    @abstractmethod
    async def save(self, subscription: Subscription) -> Subscription:
        """Persist a new or updated subscription.

        Args:
            subscription: The Subscription aggregate to persist.

        Returns:
            The persisted Subscription with any generated fields.
        """
        ...

    @abstractmethod
    async def find_by_tenant_id(self, tenant_id: uuid.UUID) -> list[Subscription]:
        """Find all subscriptions for a tenant.

        Args:
            tenant_id: The tenant UUID to scope the query.

        Returns:
            A list of subscriptions belonging to the tenant.
        """
        ...

    @abstractmethod
    async def find_active_by_tenant_id(
        self, tenant_id: uuid.UUID
    ) -> Subscription | None:
        """Find the active subscription for a tenant.

        Args:
            tenant_id: The tenant UUID to scope the query.

        Returns:
            The active Subscription, or None if no active subscription exists.
        """
        ...


class IUsageRepository(ABC):
    """Abstract repository for UsageRecord persistence.

    All implementations must enforce tenant isolation on queries.
    """

    @abstractmethod
    async def save(self, usage_record: UsageRecord) -> UsageRecord:
        """Persist a new usage record.

        Args:
            usage_record: The UsageRecord entity to persist.

        Returns:
            The persisted UsageRecord with any generated fields.
        """
        ...

    @abstractmethod
    async def find_by_tenant_and_period(
        self,
        tenant_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> list[UsageRecord]:
        """Find usage records for a tenant within a billing period.

        Args:
            tenant_id: The tenant UUID to scope the query.
            period_start: Start of the billing period (inclusive).
            period_end: End of the billing period (exclusive).

        Returns:
            A list of usage records within the period.
        """
        ...

    @abstractmethod
    async def get_usage_summary(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Get the total usage quantity for a resource type in a period.

        Args:
            tenant_id: The tenant UUID to scope the query.
            resource_type: The type of resource (e.g. "optimization", "tokens").
            period_start: Start of the billing period (inclusive).
            period_end: End of the billing period (exclusive).

        Returns:
            The sum of quantities for the specified resource type.
        """
        ...
