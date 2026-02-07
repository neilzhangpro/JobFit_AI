"""UserFactory and TenantFactory — create aggregates with validation (Factory pattern).

Factories encapsulate complex object creation logic and ensure invariants are satisfied.
"""

# TODO: Implement UserFactory class
#   - create_user(email: Email, password: str, role: Role, tenant_id: TenantId) -> User
#   - Validate business rules before creating user
#   - Hash password using PasswordHashingService
#   - Raise domain exceptions for invalid inputs

# TODO: Implement TenantFactory class
#   - create_tenant(name: str, admin_email: Email, admin_password: str) -> Tenant
#   - Create tenant with initial admin user
#   - Ensure tenant has at least one admin user (invariant)
#   - Raise domain exceptions for invalid inputs
