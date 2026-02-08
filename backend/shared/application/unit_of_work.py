"""Unit of Work interface — defines the transactional boundary for write operations.

Application services use this interface to ensure all repository operations
within a use case are committed or rolled back together.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class IUnitOfWork(ABC):
    """Abstract Unit of Work interface.

    Provides commit/rollback semantics and async context manager support.
    Concrete implementations (e.g. SqlAlchemyUnitOfWork) live in the
    infrastructure layer.
    """

    @abstractmethod
    async def commit(self) -> None:
        """Commit all pending changes in the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back all pending changes in the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> IUnitOfWork:
        """Enter the transactional context."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the transactional context, rolling back on exception."""
        ...
