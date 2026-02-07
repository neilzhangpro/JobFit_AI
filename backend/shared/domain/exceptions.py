"""Domain exception hierarchy for the entire application.

All domain-specific exceptions inherit from DomainError. This enables
consistent error handling at the API layer.
"""

# TODO(#19): Implement DomainError (base), EntityNotFoundError,
#   ValidationError, AuthorizationError, QuotaExceededError
