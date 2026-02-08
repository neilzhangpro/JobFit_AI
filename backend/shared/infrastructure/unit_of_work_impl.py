"""SQLAlchemy implementation of the Unit of Work pattern.

Wraps an AsyncSession and provides commit/rollback semantics.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from shared.application.unit_of_work import IUnitOfWork


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """Unit of Work backed by a SQLAlchemy AsyncSession.

    Usage in application services:

        async with SqlAlchemyUnitOfWork(session) as uow:
            repo.save(entity)
            await uow.commit()
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self._session.rollback()

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        """Enter the transactional context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context — automatically roll back if an exception occurred."""
        if exc_type is not None:
            await self.rollback()
