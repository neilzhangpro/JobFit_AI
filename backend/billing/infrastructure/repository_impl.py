"""SubscriptionRepository, UsageRepository — SQLAlchemy implementations.

This module contains SQLAlchemy implementations of ISubscriptionRepository
and IUsageRepository. All queries must be scoped by tenant_id to ensure
multi-tenant isolation.
"""

# TODO: Implement SubscriptionRepository class inheriting from ISubscriptionRepository
#   - Implement save method with tenant_id scoping
#   - Implement find_by_tenant_id with tenant_id filter
#   - Implement find_active_by_tenant_id with tenant_id filter
# TODO: Implement UsageRepository class inheriting from IUsageRepository
#   - Implement save method with tenant_id scoping
#   - Implement find_by_tenant_id_and_period with tenant_id filter
#   - Implement get_usage_summary with tenant_id filter
# TODO: Use UnitOfWork pattern for transactions
# TODO: Map between domain entities and SQLAlchemy models
# TODO: Add tenant isolation tests: tenant_a_cannot_see_tenant_b_data
