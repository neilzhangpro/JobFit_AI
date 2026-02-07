"""Command objects representing user intentions.

Commands are used by application services to execute use cases.
"""

from pydantic import BaseModel


class RegisterUserCommand(BaseModel):
    """Command to register a new user with a new tenant."""

    email: str
    password: str
    tenant_name: str
