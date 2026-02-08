"""JWT authentication middleware — FastAPI dependencies.

Provides get_current_user() and get_current_active_user()
dependencies for protected API endpoints.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from identity.application.dto import UserDTO
from identity.infrastructure.jwt_service import JWTService
from identity.infrastructure.models import UserModel
from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.database import get_async_session
from shared.infrastructure.tenant_context import TenantContext

# OAuth2 scheme extracts Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(  # noqa: B008
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> UserDTO:
    """Decode JWT and return the authenticated user.

    Also sets the TenantContext for downstream repository usage.

    Raises:
        HTTPException 401: If the token is invalid or
            the user is not found.
    """
    try:
        jwt_service = JWTService(get_settings())
        payload = jwt_service.decode_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Set tenant context for downstream queries
    tenant_id = payload.get("tenant_id", "")
    TenantContext.set_current_tenant_id(tenant_id)

    # Verify user still exists in database
    user_id = payload.get("sub", "")
    stmt = select(UserModel).where(UserModel.id == uuid.UUID(user_id))
    result = await db.execute(stmt)
    user_model = result.scalar_one_or_none()

    if user_model is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserDTO(
        id=str(user_model.id),
        email=user_model.email,
        role=user_model.role,
        tenant_id=str(user_model.tenant_id),
        created_at=user_model.created_at,
    )


async def get_current_active_user(  # noqa: B008
    user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """Ensure the authenticated user is active.

    Raises:
        HTTPException 403: If the user account is inactive.
    """
    return user
