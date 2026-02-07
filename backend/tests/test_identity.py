"""Tests for the Identity bounded context.

Covers: value object validation, password hashing, tenant factory,
API registration, login, token refresh, and /me endpoint.
"""

import pytest
from httpx import AsyncClient

from identity.domain.entities import Tenant, User
from identity.domain.factories import TenantFactory
from identity.domain.services import PasswordHashingService
from identity.domain.value_objects import Email, Role
from shared.domain.exceptions import ValidationError


# ===================================================================
# Domain Unit Tests
# ===================================================================
class TestEmail:
    """Tests for the Email value object."""

    def test_valid_email(self) -> None:
        """A well-formed email should be accepted."""
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_invalid_email_raises(self) -> None:
        """A malformed email should raise ValidationError."""
        with pytest.raises(ValidationError):
            Email("not-an-email")

    def test_normalization(self) -> None:
        """Email should be lowercased and stripped."""
        email = Email("  TOM@EXAMPLE.COM  ")
        assert email.value == "tom@example.com"


class TestPasswordHashing:
    """Tests for PasswordHashingService."""

    def test_hash_and_verify(self, password_hasher: PasswordHashingService) -> None:
        """A hashed password should verify correctly."""
        hashed = password_hasher.hash_password("Secret123")
        assert password_hasher.verify_password("Secret123", hashed)

    def test_wrong_password(self, password_hasher: PasswordHashingService) -> None:
        """A wrong password should not verify."""
        hashed = password_hasher.hash_password("Secret123")
        assert not password_hasher.verify_password("WrongPass", hashed)


class TestTenantFactory:
    """Tests for TenantFactory.create_tenant_with_admin."""

    def test_creates_admin(self, password_hasher: PasswordHashingService) -> None:
        """Factory should create tenant + admin user."""
        tenant, user = TenantFactory.create_tenant_with_admin(
            name="Test Corp",
            admin_email="admin@test.com",
            admin_password="Pass1234",
            hasher=password_hasher,
        )
        assert isinstance(tenant, Tenant)
        assert isinstance(user, User)
        assert user.role == Role.TENANT_ADMIN
        assert user.email.value == "admin@test.com"
        assert user.tenant_id == tenant.id

    def test_duplicate_email_raises(
        self, password_hasher: PasswordHashingService
    ) -> None:
        """Adding a user with duplicate email should raise."""
        tenant, _ = TenantFactory.create_tenant_with_admin(
            name="Test Corp",
            admin_email="admin@test.com",
            admin_password="Pass1234",
            hasher=password_hasher,
        )
        # Try adding another user with the same email
        dup_user = User(
            tenant_id=tenant.id,
            email=Email("admin@test.com"),
            hashed_password="hash",
            role=Role.MEMBER,
        )
        with pytest.raises(ValidationError):
            tenant.add_user(dup_user)


# ===================================================================
# API Integration Tests
# ===================================================================
class TestAuthAPI:
    """Integration tests for auth API endpoints."""

    @pytest.mark.asyncio
    async def test_register_returns_201(self, test_client: AsyncClient) -> None:
        """POST /api/auth/register should return 201 + tokens."""
        resp = await test_client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "Password123",
                "tenant_name": "New Corp",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_returns_token(self, test_client: AsyncClient) -> None:
        """Register then login should return tokens."""
        # Register first
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "Password123",
                "tenant_name": "Login Corp",
            },
        )
        # Login
        resp = await test_client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "Password123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password_401(self, test_client: AsyncClient) -> None:
        """Login with wrong password should return 401."""
        # Register
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "Password123",
                "tenant_name": "Wrong Corp",
            },
        )
        # Login with wrong password
        resp = await test_client.post(
            "/api/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "BadPassword",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_token_200(self, test_client: AsyncClient) -> None:
        """GET /api/auth/me with valid token returns user."""
        # Register to get token
        reg = await test_client.post(
            "/api/auth/register",
            json={
                "email": "me@example.com",
                "password": "Password123",
                "tenant_name": "Me Corp",
            },
        )
        token = reg.json()["access_token"]
        # Call /me
        resp = await test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@example.com"

    @pytest.mark.asyncio
    async def test_me_without_token_401(self, test_client: AsyncClient) -> None:
        """GET /api/auth/me without token returns 401."""
        resp = await test_client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_returns_new_token(self, test_client: AsyncClient) -> None:
        """POST /api/auth/refresh returns new access token."""
        # Register
        reg = await test_client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "Password123",
                "tenant_name": "Refresh Corp",
            },
        )
        refresh_token = reg.json()["refresh_token"]
        # Refresh
        resp = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
