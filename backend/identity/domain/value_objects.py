"""Email, Role, and TenantId value objects for the Identity context.

Value objects are immutable and compared by value, not identity.
"""

import re
import uuid
from dataclasses import dataclass
from enum import Enum

from shared.domain.base_value_object import BaseValueObject
from shared.domain.exceptions import ValidationError

# RFC 5322 simplified email regex
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@dataclass(frozen=True)
class Email(BaseValueObject):
    """Email address value object with format validation.

    Normalizes to lowercase and strips whitespace on construction.
    Raises ValidationError if the format is invalid.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize email on construction."""
        normalized = self.value.strip().lower()
        if not _EMAIL_REGEX.match(normalized):
            raise ValidationError(f"Invalid email format: {self.value}")
        # frozen dataclass requires object.__setattr__
        object.__setattr__(self, "value", normalized)


class Role(str, Enum):  # noqa: UP042
    """User role within a tenant."""

    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    MEMBER = "member"


@dataclass(frozen=True)
class TenantId(BaseValueObject):
    """Tenant identifier value object wrapping a UUID."""

    value: uuid.UUID
