"""QuotaEnforcementService — checks if tenant has remaining quota.

Domain service that enforces usage quotas by comparing current
consumption against plan-defined limits.  Pure Python — no
framework imports allowed.
"""

from __future__ import annotations

from billing.domain.entities import Subscription
from billing.domain.value_objects import get_quota_for_plan
from shared.domain.exceptions import QuotaExceededError, ValidationError


class QuotaEnforcementService:
    """Enforces plan-based usage quotas for a tenant.

    All methods receive pre-fetched data so this service stays in
    the domain layer with zero infrastructure dependencies.
    """

    def check_optimization_quota(
        self,
        subscription: Subscription,
        current_usage: int,
    ) -> bool:
        """Check whether the tenant may run another optimization.

        Args:
            subscription: The tenant's active subscription.
            current_usage: Number of optimizations consumed in the
                current billing period.

        Returns:
            True if the tenant is within limits.

        Raises:
            ValidationError: If the subscription is not active.
            QuotaExceededError: If usage has reached the plan limit.
        """
        self._assert_active(subscription)
        quota = get_quota_for_plan(subscription.plan)
        if current_usage >= quota.max_optimizations:
            raise QuotaExceededError(
                f"Optimization quota exceeded: "
                f"{current_usage}/{quota.max_optimizations} used "
                f"on {subscription.plan.value} plan"
            )
        return True

    def check_token_quota(
        self,
        subscription: Subscription,
        current_usage: int,
    ) -> bool:
        """Check whether the tenant may consume more tokens.

        Args:
            subscription: The tenant's active subscription.
            current_usage: Number of tokens consumed in the
                current billing period.

        Returns:
            True if the tenant is within limits.

        Raises:
            ValidationError: If the subscription is not active.
            QuotaExceededError: If usage has reached the plan limit.
        """
        self._assert_active(subscription)
        quota = get_quota_for_plan(subscription.plan)
        if current_usage >= quota.max_tokens:
            raise QuotaExceededError(
                f"Token quota exceeded: "
                f"{current_usage}/{quota.max_tokens} used "
                f"on {subscription.plan.value} plan"
            )
        return True

    @staticmethod
    def _assert_active(subscription: Subscription) -> None:
        """Raise if the subscription is not in active status."""
        if subscription.status != "active":
            raise ValidationError(
                f"Subscription is {subscription.status}, "
                "only active subscriptions may consume quota"
            )
