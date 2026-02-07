"""Subscription (Aggregate Root) — one active per tenant. UsageRecord (Entity).

This module contains:
- Subscription: Aggregate root representing a tenant's subscription plan
  (one active subscription per tenant)
- UsageRecord: Entity representing usage of resources (optimizations, tokens)
"""

# TODO: Implement Subscription aggregate root class
#   - tenant_id: str
#   - plan: Plan (value object)
#   - status: str (active, cancelled, expired)
#   - current_period_start: datetime
#   - current_period_end: datetime
#   - stripe_subscription_id: Optional[str]
# TODO: Implement UsageRecord entity class
#   - tenant_id: str
#   - resource_type: str (optimization, tokens, etc.)
#   - quantity: int
#   - recorded_at: datetime
# TODO: Add validation logic for subscription lifecycle
# TODO: Add domain events for subscription changes
# TODO: Ensure tenant_id is included for multi-tenant isolation
