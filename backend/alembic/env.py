"""Alembic migration environment configuration.

Supports async PostgreSQL via asyncpg. Loads DATABASE_URL from
application settings.
"""

# TODO(#9): Implement async migration runner
# TODO(#10): Import all ORM models so Alembic can detect schema changes
