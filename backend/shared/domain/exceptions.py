"""Domain exception hierarchy for the entire application.

All domain-specific exceptions inherit from DomainError. This enables
consistent error handling at the API layer.
"""


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str = "A domain error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, message: str = "Entity not found") -> None:
        super().__init__(message)


class ValidationError(DomainError):
    """Raised when a business rule or invariant is violated."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message)


class AuthenticationError(DomainError):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(DomainError):
    """Raised when the user lacks permission for the requested action."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)


class QuotaExceededError(DomainError):
    """Raised when a tenant exceeds their usage quota."""

    def __init__(self, message: str = "Quota exceeded") -> None:
        super().__init__(message)


class AgentExecutionError(DomainError):
    """Raised when an AI agent fails during pipeline execution.

    Carries the agent name and a ``recoverable`` flag so the pipeline
    orchestrator can decide whether to retry or abort.
    """

    def __init__(
        self,
        agent_name: str,
        message: str = "Agent execution failed",
        recoverable: bool = False,
    ) -> None:
        self.agent_name = agent_name
        self.recoverable = recoverable
        super().__init__(f"[{agent_name}] {message}")
