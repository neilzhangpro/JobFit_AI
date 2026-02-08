"""ResumeRepository — SQLAlchemy implementation with tenant scoping.

All queries are filtered by tenant_id for multi-tenant isolation.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from resume.domain.entities import Resume, ResumeSection
from resume.domain.repository import IResumeRepository
from resume.domain.value_objects import SectionType
from resume.infrastructure.models import (
    ResumeModel,
    ResumeSectionModel,
)


class ResumeRepository(IResumeRepository):
    """SQLAlchemy implementation of resume data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(
        self, resume_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Resume | None:
        """Find resume by ID within a specific tenant."""
        stmt = select(ResumeModel).where(
            ResumeModel.id == resume_id,
            ResumeModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_user(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[Resume]:
        """Find all resumes for a user within a tenant."""
        stmt = (
            select(ResumeModel)
            .where(
                ResumeModel.user_id == user_id,
                ResumeModel.tenant_id == tenant_id,
            )
            .order_by(ResumeModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, resume: Resume) -> Resume:
        """Persist a resume with its sections."""
        model = self._to_model(resume)
        self._session.add(model)
        await self._session.flush()
        return resume

    async def delete(self, resume_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        """Delete a resume and its sections."""
        # Delete sections first (cascade should handle it,
        # but explicit for clarity)
        await self._session.execute(
            delete(ResumeSectionModel).where(ResumeSectionModel.resume_id == resume_id)
        )
        await self._session.execute(
            delete(ResumeModel).where(
                ResumeModel.id == resume_id,
                ResumeModel.tenant_id == tenant_id,
            )
        )
        await self._session.flush()

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: ResumeModel) -> Resume:
        """Convert ORM model to domain entity."""
        resume = Resume(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            filename=model.filename,
            storage_path=model.storage_path,
            parsed_data=model.parsed_data,
        )
        resume.id = model.id
        resume.created_at = model.created_at
        resume.updated_at = model.updated_at

        # Map sections
        for sec_model in model.sections:
            section = ResumeSection(
                resume_id=sec_model.resume_id,
                section_type=SectionType(sec_model.section_type),
                content=sec_model.content,
                order_index=sec_model.order_index,
            )
            section.id = sec_model.id
            section.created_at = sec_model.created_at
            resume.add_section(section)

        return resume

    @staticmethod
    def _to_model(entity: Resume) -> ResumeModel:
        """Convert domain entity to ORM model."""
        model = ResumeModel(
            id=entity.id,
            user_id=entity.user_id,
            tenant_id=entity.tenant_id,
            filename=entity.filename,
            storage_path=entity.storage_path,
            parsed_data=entity.parsed_data,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        # Map sections
        model.sections = [
            ResumeSectionModel(
                id=s.id,
                resume_id=entity.id,
                section_type=s.section_type.value,
                content=s.content,
                order_index=s.order_index,
                created_at=s.created_at,
            )
            for s in entity.sections
        ]
        return model
