"""Tenant (Aggregate Root) and User (Entity).

Tenant must have at least one admin user. User email is unique within tenant.
"""

# TODO: Implement Tenant aggregate root class
#   - Must enforce invariant: at least one admin user
#   - Should inherit from AggregateRoot base class
#   - Include tenant_id, name, created_at, updated_at fields

# TODO: Implement User entity class
#   - Should inherit from BaseEntity
#   - Include user_id, tenant_id, email, hashed_password, role fields
#   - Email must be unique within tenant scope
#   - Include business logic methods (e.g., change_password, update_role)
