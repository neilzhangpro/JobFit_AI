"""SQLAlchemy ORM models for subscriptions and usage_records tables.

This module contains SQLAlchemy ORM models for persisting billing data.
All models must include tenant_id for multi-tenant isolation.
"""

# TODO: Implement SubscriptionModel SQLAlchemy model
#   - Fields: id, tenant_id, plan, status, current_period_start, current_period_end,
#     stripe_subscription_id, created_at, updated_at
# TODO: Implement UsageRecordModel SQLAlchemy model
#   - Fields: id, tenant_id, resource_type, quantity, recorded_at
# TODO: Ensure tenant_id is NOT NULL and indexed on both tables
# TODO: Add indexes for efficient queries (tenant_id + period, tenant_id + resource_type)
# TODO: Add foreign key constraints where appropriate
