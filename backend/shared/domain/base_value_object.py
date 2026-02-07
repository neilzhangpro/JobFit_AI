"""Base Value Object class — immutable, compared by value (not identity).

Value objects have no identity. Two value objects with the same attributes
are considered equal. They should be implemented as frozen dataclasses.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseValueObject:
    """Base class for all domain value objects.

    Value objects are immutable (frozen=True) and compared by their field
    values. Subclasses inherit this behavior — just add fields:

        @dataclass(frozen=True)
        class Email(BaseValueObject):
            value: str
    """
