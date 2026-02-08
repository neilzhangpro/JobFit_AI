"""PasswordHashingService — domain service for password hashing.

Domain services contain business logic that doesn't naturally fit
within entities or value objects.
"""

from passlib.context import CryptContext  # type: ignore[import-untyped]

# bcrypt context — configured once, reused across calls
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHashingService:
    """Handles password hashing and verification using bcrypt."""

    def hash_password(self, raw_password: str) -> str:
        """Hash a plaintext password.

        Args:
            raw_password: The plaintext password to hash.

        Returns:
            The bcrypt hash string.
        """
        result: str = _pwd_context.hash(raw_password)
        return result

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored hash.

        Args:
            raw_password: The plaintext password to check.
            hashed_password: The stored bcrypt hash.

        Returns:
            True if the password matches, False otherwise.
        """
        result: bool = _pwd_context.verify(raw_password, hashed_password)
        return result
