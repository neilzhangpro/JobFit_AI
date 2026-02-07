"""ContextVar-based tenant context for multi-tenant isolation.

Stores the current tenant_id in a ContextVar, set by TenantMiddleware.
All repository implementations read from this context to scope queries.
"""

# TODO(#25): Define _current_tenant ContextVar
# TODO(#26): Implement TenantContext class with get/set current_tenant_id
