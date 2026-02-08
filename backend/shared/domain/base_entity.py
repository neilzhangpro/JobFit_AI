"""Base Entity class providing identity (id) and timestamps (created_at, updated_at).

All domain entities across bounded contexts inherit from this class.
Entities are compared by identity (id), not by attribute values.
"""

import uuid
from datetime import datetime


class BaseEntity:
    """Base class for all domain entities.

    Entities have a unique identity (UUID) and are compared by that identity,
    not by their attribute values. Two entities with the same id are considered
    equal, regardless of other field differences.
    """

    def __init__(self) -> None:
        self.id: uuid.UUID = uuid.uuid4()
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime | None = None

    def __eq__(self, other: object) -> bool:
        """Two entities are equal if they have the same id."""
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on entity id for use in sets and dicts."""
        return hash(self.id)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
