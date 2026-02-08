"""SQLAlchemy ORM models for resumes and resume_sections tables.

ORM models map to database tables and are separate from domain entities.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database import Base


class ResumeModel(Base):
    """ORM model for the 'resumes' table."""

    __tablename__ = "resumes"
    __table_args__ = (
        Index("ix_resumes_tenant_id", "tenant_id"),
        Index("ix_resumes_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    parsed_data: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, onupdate=func.now()
    )

    # Relationship: one resume has many sections
    sections: Mapped[list["ResumeSectionModel"]] = relationship(
        "ResumeSectionModel",
        back_populates="resume",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ResumeSectionModel(Base):
    """ORM model for the 'resume_sections' table."""

    __tablename__ = "resume_sections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship: each section belongs to one resume
    resume: Mapped["ResumeModel"] = relationship(
        "ResumeModel", back_populates="sections"
    )
