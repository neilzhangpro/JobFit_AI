"""ResumeApplicationService — orchestrates resume use cases.

Coordinates between domain objects, infrastructure adapters,
and the unit of work for transactional consistency.
"""

import uuid

from resume.application.commands import UploadResumeCommand
from resume.application.dto import (
    ResumeDetailDTO,
    ResumeListItemDTO,
    ResumeSectionDTO,
    UploadResumeResponse,
)
from resume.domain.factories import ResumeFactory
from resume.domain.repository import IResumeRepository
from resume.domain.services import ResumeParsingDomainService
from resume.infrastructure.file_storage import FileStorageAdapter
from resume.infrastructure.pdf_parser import PDFParser
from resume.infrastructure.vector_store import VectorStoreAdapter
from shared.application.unit_of_work import IUnitOfWork
from shared.domain.exceptions import EntityNotFoundError


class ResumeApplicationService:
    """Orchestrates resume upload, retrieval, and deletion."""

    def __init__(
        self,
        repo: IResumeRepository,
        file_storage: FileStorageAdapter,
        pdf_parser: PDFParser,
        parsing_service: ResumeParsingDomainService,
        vector_store: VectorStoreAdapter,
        uow: IUnitOfWork,
    ) -> None:
        self._repo = repo
        self._storage = file_storage
        self._parser = pdf_parser
        self._parsing = parsing_service
        self._vectors = vector_store
        self._uow = uow

    async def upload(self, cmd: UploadResumeCommand) -> UploadResumeResponse:
        """Upload, parse, and store a resume.

        Args:
            cmd: Upload command with file bytes and user info.

        Returns:
            UploadResumeResponse with resume ID and section count.
        """
        # 1. Store file in S3/MinIO
        storage_path = self._storage.store(
            tenant_id=cmd.tenant_id,
            user_id=cmd.user_id,
            filename=cmd.filename,
            file_bytes=cmd.file_bytes,
        )

        # 2. Extract text from PDF
        raw_text = self._parser.extract_text(cmd.file_bytes)

        # 3. Create Resume aggregate via factory
        resume = ResumeFactory.create_from_upload(
            user_id=uuid.UUID(cmd.user_id),
            tenant_id=uuid.UUID(cmd.tenant_id),
            filename=cmd.filename,
            storage_path=storage_path,
            raw_text=raw_text,
            parsing_service=self._parsing,
        )

        # 4. Persist to database
        await self._repo.save(resume)
        await self._uow.commit()

        # 5. Store embeddings (stub for now)
        self._vectors.store_embeddings(
            tenant_id=cmd.tenant_id,
            resume_id=str(resume.id),
            sections=[
                {
                    "type": s.section_type.value,
                    "content": s.content,
                }
                for s in resume.sections
            ],
        )

        return UploadResumeResponse(
            id=str(resume.id),
            filename=resume.filename,
            section_count=resume.section_count,
            message="Resume uploaded and parsed successfully",
        )

    async def get_resume(self, resume_id: str, tenant_id: str) -> ResumeDetailDTO:
        """Get a resume with all its sections.

        Raises:
            EntityNotFoundError: If resume not found.
        """
        resume = await self._repo.find_by_id(uuid.UUID(resume_id), uuid.UUID(tenant_id))
        if resume is None:
            raise EntityNotFoundError(f"Resume {resume_id} not found")

        return ResumeDetailDTO(
            id=str(resume.id),
            filename=resume.filename,
            storage_path=resume.storage_path,
            sections=[
                ResumeSectionDTO(
                    id=str(s.id),
                    section_type=s.section_type.value,
                    content=s.content,
                    order_index=s.order_index,
                )
                for s in resume.sections
            ],
            created_at=resume.created_at,
        )

    async def list_resumes(
        self, user_id: str, tenant_id: str
    ) -> list[ResumeListItemDTO]:
        """List all resumes for the current user."""
        resumes = await self._repo.find_by_user(
            uuid.UUID(user_id), uuid.UUID(tenant_id)
        )
        return [
            ResumeListItemDTO(
                id=str(r.id),
                filename=r.filename,
                section_count=r.section_count,
                created_at=r.created_at,
            )
            for r in resumes
        ]

    async def delete_resume(self, resume_id: str, tenant_id: str) -> None:
        """Delete a resume from DB and file storage.

        Raises:
            EntityNotFoundError: If resume not found.
        """
        resume = await self._repo.find_by_id(uuid.UUID(resume_id), uuid.UUID(tenant_id))
        if resume is None:
            raise EntityNotFoundError(f"Resume {resume_id} not found")

        # Delete from storage
        self._storage.delete(resume.storage_path)

        # Delete from database
        await self._repo.delete(uuid.UUID(resume_id), uuid.UUID(tenant_id))
        await self._uow.commit()
