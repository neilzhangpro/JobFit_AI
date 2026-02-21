"""In-process event bus implementation (Observer pattern).

Routes domain events to registered async handlers. Used for
cross-context communication (e.g. OptimizationCompleted -> Billing
usage tracking).

Errors in one handler are logged but never propagate to callers,
so a failing handler cannot break the publishing aggregate's flow.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from shared.domain.domain_event import DomainEvent, EventHandler, IEventBus

logger = logging.getLogger(__name__)


class InProcessEventBus(IEventBus):
    """In-memory event bus that dispatches events to async handlers.

    Thread-safety note: this implementation is intended for use within
    a single asyncio event loop.  Handler registration typically happens
    at application startup before requests are served.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register an async handler for a specific event type.

        Args:
            event_type: The event type string to listen for.
            handler: An async callable accepting a DomainEvent.
        """
        self._handlers[event_type].append(handler)
        logger.debug(
            "Handler %s subscribed to '%s'",
            handler.__qualname__,
            event_type,
        )

    async def publish(self, event: DomainEvent) -> None:
        """Fan out a domain event to all subscribed handlers.

        If no handlers are registered for the event type, the event
        is silently ignored.  If a handler raises, the exception is
        logged and remaining handlers still execute.

        Args:
            event: The domain event to dispatch.
        """
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Handler %s failed for event '%s' (id=%s)",
                    handler.__qualname__,
                    event.event_type,
                    event.event_id,
                )
