"""AuthApplicationService — orchestrates auth use cases.

Application services coordinate between domain objects and
infrastructure, but contain no business rules themselves.
"""

from identity.application.commands import RegisterUserCommand
from identity.application.dto import (
    LoginRequest,
    TokenResponse,
    UserDTO,
)
from identity.domain.factories import TenantFactory
from identity.domain.repository import (
    ITenantRepository,
    IUserRepository,
)
from identity.domain.services import PasswordHashingService
from identity.infrastructure.jwt_service import JWTService
from shared.application.unit_of_work import IUnitOfWork
from shared.domain.exceptions import AuthenticationError


class AuthApplicationService:
    """Orchestrates registration, login, and token refresh."""

    def __init__(
        self,
        user_repo: IUserRepository,
        tenant_repo: ITenantRepository,
        hasher: PasswordHashingService,
        jwt_service: JWTService,
        uow: IUnitOfWork,
    ) -> None:
        self._user_repo = user_repo
        self._tenant_repo = tenant_repo
        self._hasher = hasher
        self._jwt = jwt_service
        self._uow = uow

    async def register(self, cmd: RegisterUserCommand) -> TokenResponse:
        """Register a new tenant with an admin user.

        Args:
            cmd: Registration command with email, password,
                and tenant name.

        Returns:
            TokenResponse with access and refresh tokens.
        """
        # Domain layer creates and validates the aggregates
        tenant, admin_user = TenantFactory.create_tenant_with_admin(
            name=cmd.tenant_name,
            admin_email=cmd.email,
            admin_password=cmd.password,
            hasher=self._hasher,
        )

        # Persist via repositories
        await self._tenant_repo.save(tenant)
        await self._user_repo.save(admin_user)
        await self._uow.commit()

        # Issue JWT tokens
        return self._issue_tokens(admin_user)

    async def login(self, cmd: LoginRequest) -> TokenResponse:
        """Authenticate a user and issue tokens.

        Args:
            cmd: Login request with email and password.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        # Login is a special case: tenant context is not set yet,
        # so we search across all tenants
        user = await self._user_repo.find_by_email_any_tenant(cmd.email)
        if user is None:
            raise AuthenticationError("Invalid credentials")

        if not user.verify_password(cmd.password, self._hasher):
            raise AuthenticationError("Invalid credentials")

        return self._issue_tokens(user)

    async def refresh_token(self, token: str) -> TokenResponse:
        """Issue new tokens using a valid refresh token.

        Args:
            token: The refresh token string.

        Returns:
            TokenResponse with new access and refresh tokens.

        Raises:
            AuthenticationError: If the refresh token is
                invalid or the user no longer exists.
        """
        payload = self._jwt.decode_token(token)

        if payload.get("type") != "refresh":
            raise AuthenticationError("Token is not a refresh token")

        import uuid

        user_id = uuid.UUID(payload["sub"])
        user = await self._user_repo.find_by_id(user_id)

        if user is None:
            raise AuthenticationError("User no longer exists")

        return self._issue_tokens(user)

    def _issue_tokens(self, user: object) -> TokenResponse:
        """Create access + refresh tokens for a user."""
        # user is typed as object to keep import simple;
        # at runtime it's identity.domain.entities.User
        access = self._jwt.create_access_token(
            user_id=str(user.id),  # type: ignore[attr-defined]
            tenant_id=str(user.tenant_id),  # type: ignore[attr-defined]
            role=user.role.value,  # type: ignore[attr-defined]
        )
        refresh = self._jwt.create_refresh_token(
            user_id=str(user.id),  # type: ignore[attr-defined]
            tenant_id=str(user.tenant_id),  # type: ignore[attr-defined]
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=(self._jwt.access_token_expire_minutes * 60),
        )


def user_to_dto(user: object) -> UserDTO:
    """Convert a domain User entity to a UserDTO."""
    return UserDTO(
        id=str(user.id),  # type: ignore[attr-defined]
        email=user.email.value,  # type: ignore[attr-defined]
        role=user.role.value,  # type: ignore[attr-defined]
        tenant_id=str(user.tenant_id),  # type: ignore[attr-defined]
        created_at=user.created_at,  # type: ignore[attr-defined]
    )
