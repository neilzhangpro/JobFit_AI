"""Base Entity class providing identity (id) and timestamps (created_at, updated_at).

All domain entities across bounded contexts inherit from this class.
Entities are compared by identity (id), not by attribute values.
"""

# TODO(#11): Implement BaseEntity with id (UUID), created_at, updated_at
# TODO(#12): Implement __eq__ and __hash__ based on id
