"""ResumeRepository — SQLAlchemy implementation with tenant_id scoping.

Implements IResumeRepository interface. All queries are automatically
filtered by the current tenant_id from TenantContext.
"""

# TODO(#59): Implement ResumeRepository with tenant-scoped CRUD operations
