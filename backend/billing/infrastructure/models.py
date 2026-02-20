"""SQLAlchemy ORM models for subscriptions and usage_records tables.

ORM models map to database tables and are separate from domain entities.
The repository layer converts between ORM models and domain objects.
All models include tenant_id (NOT NULL, indexed) for multi-tenant isolation.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class SubscriptionModel(Base):
    """ORM model for the 'subscriptions' table."""

    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, onupdate=func.now()
    )


class UsageRecordModel(Base):
    """ORM model for the 'usage_records' table."""

    __tablename__ = "usage_records"
    __table_args__ = (
        Index("ix_usage_records_tenant_id", "tenant_id"),
        Index(
            "ix_usage_records_tenant_resource",
            "tenant_id",
            "resource_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
