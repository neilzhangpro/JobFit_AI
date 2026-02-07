"""Domain Event base class and in-process event bus interface.

Domain events represent something meaningful that happened in the domain.
They are published by aggregate roots and consumed by event handlers
in other bounded contexts (Observer pattern).
"""

# TODO(#17): Implement DomainEvent base class with event_type, timestamp, payload
# TODO(#18): Define IEventBus interface with publish() and subscribe() methods
