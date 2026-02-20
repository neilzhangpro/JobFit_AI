"""Shared test fixtures for the JobFit AI backend test suite.

Provides async database sessions, test clients, and common
helper objects for unit and integration tests.
"""

# Set test env vars BEFORE any app imports to prevent
# database.py from connecting to PostgreSQL at module load.
# Use file-based SQLite so all connections see the same DB.
import os
import tempfile

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as _f:
    _test_db_path = _f.name
_test_db_url = f"sqlite+aiosqlite:///{_test_db_path}"

os.environ["DATABASE_URL"] = _test_db_url
os.environ["APP_ENV"] = "test"

import asyncio  # noqa: E402
from collections.abc import AsyncGenerator, Generator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import ORM models so they register with Base.metadata
from billing.infrastructure.models import (  # noqa: E402, F401
    SubscriptionModel,
    UsageRecordModel,
)
from config import Settings  # noqa: E402
from identity.domain.services import PasswordHashingService  # noqa: E402
from identity.infrastructure.jwt_service import JWTService  # noqa: E402
from identity.infrastructure.models import TenantModel, UserModel  # noqa: E402, F401
from resume.infrastructure.models import (  # noqa: E402, F401
    ResumeModel,
    ResumeSectionModel,
)
from shared.infrastructure.database import Base, get_async_session  # noqa: E402


# --- Event loop fixture (required by pytest-asyncio) ---
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# --- Test settings ---
@pytest.fixture
def test_settings() -> Settings:
    """Return settings configured for testing."""
    return Settings(
        database_url=_test_db_url,
        jwt_secret_key="test-secret-key-for-testing-only",
        jwt_access_token_expire_minutes=5,
        jwt_refresh_token_expire_days=1,
        app_env="test",
    )


# --- Async database session (file-based SQLite) ---
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables in file-based SQLite, yield session."""
    engine = create_async_engine(_test_db_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


# --- Test FastAPI app with dependency overrides ---
@pytest.fixture
async def test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client against the test app."""
    from main import app

    # Override the DB session dependency to use the test session
    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    # Restore original dependencies
    app.dependency_overrides.clear()


# --- Common helper fixtures ---
@pytest.fixture
def jwt_service(test_settings: Settings) -> JWTService:
    """Return a JWTService configured for testing."""
    return JWTService(test_settings)


@pytest.fixture
def password_hasher() -> PasswordHashingService:
    """Return a PasswordHashingService instance."""
    return PasswordHashingService()
