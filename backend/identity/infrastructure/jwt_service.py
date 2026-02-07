"""JWT token generation and validation using python-jose.

JWT service handles access token and refresh token creation and validation.
"""

# TODO: Implement JWTService class
#   - generate_access_token(user_id: str, tenant_id: str, role: str) -> str
#   - generate_refresh_token(user_id: str, tenant_id: str) -> str
#   - validate_token(token: str) -> dict: Decode and validate JWT
#   - Use python-jose library (JWT.encode, JWT.decode)
#   - Include expiration time configuration
#   - Handle JWT exceptions (ExpiredSignatureError, InvalidTokenError, etc.)
#   - Read secret key and algorithm from configuration
