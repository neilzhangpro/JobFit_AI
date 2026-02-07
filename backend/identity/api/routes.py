"""FastAPI routes: POST /auth/register, POST /auth/login, POST /auth/refresh, GET /tenants.

API routes handle HTTP requests and delegate to application services.
"""

# TODO: Implement POST /auth/register route
#   - Accept RegisterRequest DTO
#   - Call AuthApplicationService.register()
#   - Return TokenResponse DTO
#   - Include error handling and HTTP status codes
#   - Use dependency injection for application service

# TODO: Implement POST /auth/login route
#   - Accept LoginRequest DTO
#   - Call AuthApplicationService.login()
#   - Return TokenResponse DTO
#   - Include error handling and HTTP status codes
#   - Use dependency injection for application service

# TODO: Implement POST /auth/refresh route
#   - Accept refresh token in request body
#   - Call AuthApplicationService.refresh_token()
#   - Return TokenResponse DTO
#   - Include error handling and HTTP status codes
#   - Use dependency injection for application service

# TODO: Implement GET /tenants route
#   - Require authentication (use auth middleware)
#   - Require platform_admin role (authorization check)
#   - Call TenantApplicationService.list_tenants()
#   - Return List[TenantDTO]
#   - Include error handling and HTTP status codes
#   - Use dependency injection for application service

# TODO: Register routes with FastAPI router
#   - Create APIRouter instance
#   - Include all routes
#   - Add router tags and descriptions
