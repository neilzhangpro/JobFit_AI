"""SQLAlchemy async engine and session factory (Singleton pattern).

Provides get_async_session() dependency for FastAPI injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

# --- Async Engine (Singleton) ---
engine = create_async_engine(
    get_settings().database_url,
    echo=get_settings().is_development,
    pool_pre_ping=True,
)

# --- Session Factory ---
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Base Model for all ORM models ---
class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


# --- FastAPI Dependency ---
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-closed after request."""
    async with AsyncSessionLocal() as session:
        yield session
