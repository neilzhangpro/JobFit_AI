"""DTOs for data exchange between API and Application layers.

All request/response models use Pydantic for validation.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)
    tenant_name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response containing JWT access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserDTO(BaseModel):
    """Public user representation (excludes password hash)."""

    id: str
    email: str
    role: str
    tenant_id: str
    created_at: datetime
