"""RegisterRequest, LoginRequest, TokenResponse, UserDTO DTOs.

DTOs (Data Transfer Objects) are used for data exchange between API and
application layers.
"""

# TODO: Implement RegisterRequest DTO
#   - Fields: email, password, tenant_name (optional), role (optional)
#   - Include Pydantic validators for email format and password strength

# TODO: Implement LoginRequest DTO
#   - Fields: email, password
#   - Include Pydantic validators

# TODO: Implement TokenResponse DTO
#   - Fields: access_token, refresh_token, token_type, expires_in
#   - Include Pydantic validators

# TODO: Implement UserDTO DTO
#   - Fields: user_id, email, role, tenant_id, created_at
#   - Exclude sensitive fields (password hash)
#   - Include Pydantic validators

# TODO: Implement TenantDTO DTO
#   - Fields: tenant_id, name, created_at, updated_at
#   - Include Pydantic validators
