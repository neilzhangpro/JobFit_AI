"""JWT authentication middleware.

Validates the Authorization header, decodes the JWT token, extracts
user_id and tenant_id, and injects them into the request state.
"""

# TODO(#29): Implement AuthMiddleware with JWT validation
# TODO(#30): Add get_current_user() FastAPI dependency
