"""ContextVar-based tenant context for multi-tenant isolation.

Stores the current tenant_id in a ContextVar, set by TenantMiddleware.
All repository implementations read from this context to scope queries.
"""

from contextvars import ContextVar

from shared.domain.exceptions import AuthorizationError

# Module-level ContextVar — each async task gets its own copy automatically
_current_tenant: ContextVar[str | None] = ContextVar(
    "current_tenant",
    default=None,
)


class TenantContext:
    """Manages the current tenant_id for multi-tenant data isolation.

    The auth middleware sets the tenant_id after JWT validation, and
    repository implementations read it to scope all database queries.
    """

    @staticmethod
    def get_current_tenant_id() -> str:
        """Return the current tenant_id.

        Raises:
            AuthorizationError: If tenant context has not been set
                (e.g. unauthenticated request reaching a protected path).
        """
        tenant_id = _current_tenant.get()
        if tenant_id is None:
            raise AuthorizationError("Tenant context not set")
        return tenant_id

    @staticmethod
    def set_current_tenant_id(tenant_id: str) -> None:
        """Set the current tenant_id (called by auth middleware)."""
        _current_tenant.set(tenant_id)

    @staticmethod
    def clear() -> None:
        """Reset tenant context to None (called after request completes)."""
        _current_tenant.set(None)
