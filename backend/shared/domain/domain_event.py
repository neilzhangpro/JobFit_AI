"""Domain Event base class and in-process event bus interface.

Domain events represent something meaningful that happened in the domain.
They are published by aggregate roots and consumed by event handlers
in other bounded contexts (Observer pattern).
"""

import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Events are immutable records of something that happened in the domain.
    Aggregate roots collect events via _add_event(), and the application
    layer dispatches them after persistence.
    """

    event_type: str = ""
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = field(default_factory=dict)


# Type alias for event handler functions
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class IEventBus(ABC):
    """Interface for the domain event bus (Observer pattern).

    Concrete implementations live in the infrastructure layer.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers."""
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register a handler for a specific event type."""
        ...
