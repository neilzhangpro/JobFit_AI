"""Base Aggregate Root class — extends BaseEntity with domain event support.

Aggregate roots are the consistency boundaries in DDD. They collect domain
events via _add_event() and expose them via collect_events() for the
application layer to dispatch after persistence.
"""

from shared.domain.base_entity import BaseEntity
from shared.domain.domain_event import DomainEvent


class AggregateRoot(BaseEntity):
    """Base class for all aggregate roots.

    Aggregate roots manage a collection of domain events. Business methods
    call _add_event() to record events, and the application layer calls
    collect_events() after committing to dispatch them via the event bus.
    """

    def __init__(self) -> None:
        super().__init__()
        self._events: list[DomainEvent] = []

    def _add_event(self, event: DomainEvent) -> None:
        """Record a domain event (called by business methods)."""
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Return all pending events and clear the internal list.

        The application layer calls this after a successful commit to
        dispatch events via the event bus.
        """
        events = self._events.copy()
        self._events.clear()
        return events
