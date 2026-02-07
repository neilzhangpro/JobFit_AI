"""AuthApplicationService (login/register) and TenantApplicationService (CRUD).

Application services orchestrate use cases and coordinate between domain and infrastructure.
"""

# TODO: Implement AuthApplicationService class
#   - register(dto: RegisterRequest) -> TokenResponse: Register new user/tenant
#   - login(dto: LoginRequest) -> TokenResponse: Authenticate user and return JWT
#   - refresh_token(refresh_token: str) -> TokenResponse: Generate new access token
#   - Use UserRepository, TenantRepository, PasswordHashingService, JWTService
#   - Handle domain exceptions and convert to application exceptions

# TODO: Implement TenantApplicationService class
#   - create_tenant(command: CreateTenantCommand) -> TenantDTO: Create new tenant
#   - get_tenant(tenant_id: str) -> TenantDTO: Retrieve tenant by ID
#   - list_tenants() -> List[TenantDTO]: List all tenants (platform admin only)
#   - Use TenantRepository and enforce authorization rules
