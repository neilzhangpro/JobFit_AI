"""JWT token generation and validation using python-jose.

Handles access token and refresh token lifecycle.
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from config import Settings
from shared.domain.exceptions import AuthenticationError

_ALGORITHM = "HS256"


class JWTService:
    """Manages JWT access and refresh tokens."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._access_expire_min = settings.jwt_access_token_expire_minutes
        self._refresh_expire_days = settings.jwt_refresh_token_expire_days

    @property
    def access_token_expire_minutes(self) -> int:
        """Return configured access token expiry in minutes."""
        return self._access_expire_min

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
    ) -> str:
        """Create a short-lived access token.

        Args:
            user_id: The user's UUID string.
            tenant_id: The tenant's UUID string.
            role: The user's role (e.g. "tenant_admin").

        Returns:
            Encoded JWT string.
        """
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire_min),
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
    ) -> str:
        """Create a long-lived refresh token.

        Args:
            user_id: The user's UUID string.
            tenant_id: The tenant's UUID string.

        Returns:
            Encoded JWT string.
        """
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire_days),
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token.

        Args:
            token: The encoded JWT string.

        Returns:
            The decoded payload as a dict.

        Raises:
            AuthenticationError: If the token is expired,
                malformed, or otherwise invalid.
        """
        try:
            return jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
            )
        except ExpiredSignatureError as e:
            raise AuthenticationError("Token has expired") from e
        except JWTError as e:
            raise AuthenticationError("Invalid token") from e
