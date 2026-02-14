"""Plan enum (free/pro/enterprise), Quota (max_optimizations, max_tokens per month).

This module contains value objects for the billing domain:
- Plan: Enumeration of subscription plans (free, pro, enterprise)
- Quota: Represents usage limits for a plan (max optimizations, max tokens per month)
- get_quota_for_plan: Maps a Plan to its default Quota limits
"""

from dataclasses import dataclass
from enum import Enum

from shared.domain.base_value_object import BaseValueObject
from shared.domain.exceptions import ValidationError


class Plan(str, Enum):  # noqa: UP042
    """Subscription plan tier.

    Each plan defines a different level of access and quota limits
    for the tenant's users.
    """

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class Quota(BaseValueObject):
    """Usage limits for a subscription plan.

    Immutable value object representing the maximum number of
    optimizations and tokens a tenant may consume per billing period.

    Args:
        max_optimizations: Maximum optimization runs per month.
        max_tokens: Maximum LLM tokens per month.

    Raises:
        ValidationError: If either limit is negative.
    """

    max_optimizations: int
    max_tokens: int

    def __post_init__(self) -> None:
        """Validate that quota limits are non-negative."""
        if self.max_optimizations < 0:
            raise ValidationError(
                f"max_optimizations must be >= 0, got {self.max_optimizations}"
            )
        if self.max_tokens < 0:
            raise ValidationError(f"max_tokens must be >= 0, got {self.max_tokens}")


# --- Plan-to-Quota mapping (constants) ---

_FREE_QUOTA = Quota(max_optimizations=3, max_tokens=50_000)
_PRO_QUOTA = Quota(max_optimizations=30, max_tokens=500_000)
_ENTERPRISE_QUOTA = Quota(max_optimizations=200, max_tokens=5_000_000)

_PLAN_QUOTA_MAP: dict[Plan, Quota] = {
    Plan.FREE: _FREE_QUOTA,
    Plan.PRO: _PRO_QUOTA,
    Plan.ENTERPRISE: _ENTERPRISE_QUOTA,
}


def get_quota_for_plan(plan: Plan) -> Quota:
    """Return the default Quota for a given Plan.

    Args:
        plan: The subscription plan tier.

    Returns:
        The Quota value object with limits for the plan.

    Raises:
        ValidationError: If the plan is not recognized.
    """
    quota = _PLAN_QUOTA_MAP.get(plan)
    if quota is None:
        raise ValidationError(f"Unknown plan: {plan}")
    return quota
