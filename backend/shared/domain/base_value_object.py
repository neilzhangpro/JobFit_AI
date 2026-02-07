"""Base Value Object class — immutable, compared by value (not identity).

Value objects have no identity. Two value objects with the same attributes
are considered equal. They should be implemented as frozen dataclasses.
"""

# TODO(#13): Implement BaseValueObject with frozen=True dataclass pattern
# TODO(#14): Implement __eq__ and __hash__ based on all fields
