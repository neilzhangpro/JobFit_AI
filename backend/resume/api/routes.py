"""FastAPI routes for the Resume bounded context.

POST /upload, GET /, GET /{resume_id}, DELETE /{resume_id}.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from identity.application.dto import UserDTO
from resume.application.commands import UploadResumeCommand
from resume.application.dto import (
    ResumeDetailDTO,
    ResumeListItemDTO,
    UploadResumeResponse,
)
from resume.application.services import ResumeApplicationService
from resume.domain.services import ResumeParsingDomainService
from resume.infrastructure.file_storage import FileStorageAdapter
from resume.infrastructure.pdf_parser import PDFParser
from resume.infrastructure.repository_impl import ResumeRepository
from resume.infrastructure.vector_store import VectorStoreAdapter
from shared.domain.exceptions import EntityNotFoundError
from shared.infrastructure.database import get_async_session
from shared.infrastructure.unit_of_work_impl import (
    SqlAlchemyUnitOfWork,
)
from shared.middleware.auth_middleware import (
    get_current_active_user,
)

router = APIRouter()

# Max upload size in bytes (from settings)
_MAX_UPLOAD_BYTES = get_settings().max_upload_size_mb * 1024 * 1024


# --- Dependency: assemble ResumeApplicationService ---
async def get_resume_service(  # noqa: B008
    session: AsyncSession = Depends(get_async_session),
) -> ResumeApplicationService:
    """Build ResumeApplicationService with all dependencies."""
    settings = get_settings()
    return ResumeApplicationService(
        repo=ResumeRepository(session),
        file_storage=FileStorageAdapter(settings),
        pdf_parser=PDFParser(),
        parsing_service=ResumeParsingDomainService(),
        vector_store=VectorStoreAdapter(),
        uow=SqlAlchemyUnitOfWork(session),
    )


@router.post(
    "/upload",
    response_model=UploadResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(  # noqa: B008
    file: UploadFile,
    user: UserDTO = Depends(get_current_active_user),
    service: ResumeApplicationService = Depends(get_resume_service),
) -> UploadResumeResponse:
    """Upload and parse a PDF resume."""
    # Validate file type
    if file.content_type != "application/pdf" and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(f"File too large. Max size: {get_settings().max_upload_size_mb}MB"),
        )

    try:
        cmd = UploadResumeCommand(
            user_id=user.id,
            tenant_id=user.tenant_id,
            filename=file.filename or "resume.pdf",
            file_bytes=file_bytes,
        )
        return await service.upload(cmd)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get(
    "/",
    response_model=list[ResumeListItemDTO],
)
async def list_resumes(  # noqa: B008
    user: UserDTO = Depends(get_current_active_user),
    service: ResumeApplicationService = Depends(get_resume_service),
) -> list[ResumeListItemDTO]:
    """List all resumes for the current user."""
    return await service.list_resumes(user_id=user.id, tenant_id=user.tenant_id)


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailDTO,
)
async def get_resume(  # noqa: B008
    resume_id: str,
    user: UserDTO = Depends(get_current_active_user),
    service: ResumeApplicationService = Depends(get_resume_service),
) -> ResumeDetailDTO:
    """Get resume detail with all parsed sections."""
    try:
        return await service.get_resume(resume_id=resume_id, tenant_id=user.tenant_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resume(  # noqa: B008
    resume_id: str,
    user: UserDTO = Depends(get_current_active_user),
    service: ResumeApplicationService = Depends(get_resume_service),
) -> None:
    """Delete a resume and its stored file."""
    try:
        await service.delete_resume(resume_id=resume_id, tenant_id=user.tenant_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
