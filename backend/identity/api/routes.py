"""FastAPI routes for the Identity bounded context.

POST /register, POST /login, POST /refresh, GET /me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from identity.application.commands import RegisterUserCommand
from identity.application.dto import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserDTO,
)
from identity.application.services import AuthApplicationService
from identity.domain.services import PasswordHashingService
from identity.infrastructure.jwt_service import JWTService
from identity.infrastructure.repository_impl import (
    TenantRepository,
    UserRepository,
)
from shared.domain.exceptions import (
    AuthenticationError,
    ValidationError,
)
from shared.infrastructure.database import get_async_session
from shared.infrastructure.unit_of_work_impl import (
    SqlAlchemyUnitOfWork,
)
from shared.middleware.auth_middleware import (
    get_current_active_user,
)

router = APIRouter()


# --- Dependency: assemble AuthApplicationService ---
async def get_auth_service(  # noqa: B008
    session: AsyncSession = Depends(get_async_session),
) -> AuthApplicationService:
    """Build AuthApplicationService with all dependencies."""
    settings = get_settings()
    return AuthApplicationService(
        user_repo=UserRepository(session),
        tenant_repo=TenantRepository(session),
        hasher=PasswordHashingService(),
        jwt_service=JWTService(settings),
        uow=SqlAlchemyUnitOfWork(session),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(  # noqa: B008
    body: RegisterRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new user and tenant."""
    try:
        cmd = RegisterUserCommand(
            email=body.email,
            password=body.password,
            tenant_name=body.tenant_name,
        )
        return await service.register(cmd)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(  # noqa: B008
    body: LoginRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate a user and return JWT tokens."""
    try:
        return await service.login(body)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(  # noqa: B008
    body: RefreshRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh an access token using a refresh token."""
    try:
        return await service.refresh_token(body.refresh_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e


@router.get("/me", response_model=UserDTO)
async def get_me(  # noqa: B008
    user: UserDTO = Depends(get_current_active_user),
) -> UserDTO:
    """Return the currently authenticated user's info."""
    return user
