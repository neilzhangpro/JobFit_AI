"""SQLAlchemy ORM models for tenants and users tables.

ORM models represent database tables and should be separate from domain entities.
"""

# TODO: Implement TenantModel SQLAlchemy model
#   - Table name: tenants
#   - Fields: id (UUID, primary key), name (String), tenant_id (UUID, unique, indexed)
#   - Include created_at, updated_at timestamps
#   - Include relationship to UserModel (one-to-many)
#   - Ensure tenant_id is NOT NULL

# TODO: Implement UserModel SQLAlchemy model
#   - Table name: users
#   - Fields: id (UUID, primary key), tenant_id (UUID, foreign key, indexed)
#   - Fields: email (String, unique within tenant), hashed_password (String)
#   - Fields: role (Enum: platform_admin/tenant_admin/member)
#   - Include created_at, updated_at timestamps
#   - Include unique constraint on (tenant_id, email)
#   - Ensure tenant_id is NOT NULL
