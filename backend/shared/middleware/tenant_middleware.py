"""Tenant context middleware.

Reads tenant_id from the authenticated request and sets it in the
TenantContext ContextVar for downstream repository usage.
"""

# TODO(#31): Implement TenantMiddleware setting ContextVar from JWT claims
