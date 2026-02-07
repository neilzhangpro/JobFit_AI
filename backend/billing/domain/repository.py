"""ISubscriptionRepository and IUsageRepository interfaces (ABC).

This module defines repository interfaces for Subscription and UsageRecord entities.
All implementations must enforce tenant isolation.
"""

# TODO: Define ISubscriptionRepository abstract base class
#   - Methods: save, find_by_tenant_id, find_active_by_tenant_id
# TODO: Define IUsageRepository abstract base class
#   - Methods: save, find_by_tenant_id_and_period, get_usage_summary
# TODO: Ensure all methods enforce tenant_id scoping
# TODO: Add type hints for domain entities
# TODO: Follow repository pattern from other bounded contexts
