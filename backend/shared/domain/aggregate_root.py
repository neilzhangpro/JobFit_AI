"""Base Aggregate Root class — extends BaseEntity with domain event support.

Aggregate roots are the consistency boundaries in DDD. They collect domain
events via _add_event() and expose them via collect_events() for the
application layer to dispatch after persistence.
"""

# TODO(#15): Implement AggregateRoot extending BaseEntity
# TODO(#16): Add _events list, _add_event(), collect_events() methods
