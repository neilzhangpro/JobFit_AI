"""Tests for the Resume bounded context.

Covers: section types, parsing service, resume factory,
PDF parser, API upload/list/detail/delete endpoints.
"""

import io
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from resume.application.services import ResumeApplicationService
from resume.domain.entities import Resume, ResumeSection
from resume.domain.factories import ResumeFactory
from resume.domain.services import ResumeParsingDomainService
from resume.domain.value_objects import SectionType
from resume.infrastructure.pdf_parser import PDFParser
from resume.infrastructure.repository_impl import ResumeRepository
from resume.infrastructure.vector_store import VectorStoreAdapter
from shared.infrastructure.unit_of_work_impl import SqlAlchemyUnitOfWork


# --- Minimal valid PDF bytes for testing ---
def _make_test_pdf(text: str = "Test resume content") -> bytes:
    """Create a minimal valid PDF using PyPDF2 PdfWriter."""
    from PyPDF2 import PdfWriter  # type: ignore[import-untyped]

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Subject": text})

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _mock_file_storage() -> MagicMock:
    """Create a mock FileStorageAdapter."""
    mock = MagicMock()
    mock.store.return_value = "test/path/resume.pdf"
    mock.retrieve.return_value = b"pdf bytes"
    mock.delete.return_value = None
    return mock


# ===================================================================
# Domain Unit Tests
# ===================================================================
class TestSectionType:
    """Tests for SectionType enum."""

    def test_enum_has_six_values(self) -> None:
        """SectionType should have exactly 6 values."""
        values = list(SectionType)
        assert len(values) == 6

    def test_enum_values(self) -> None:
        """SectionType values should match expected strings."""
        assert SectionType.EDUCATION == "education"
        assert SectionType.EXPERIENCE == "experience"
        assert SectionType.PROJECTS == "projects"
        assert SectionType.SKILLS == "skills"
        assert SectionType.CERTIFICATIONS == "certifications"
        assert SectionType.SUMMARY == "summary"


class TestResumeParsingService:
    """Tests for ResumeParsingDomainService."""

    def test_splits_text_into_sections(self) -> None:
        """Service should split text by recognized headings."""
        service = ResumeParsingDomainService()
        raw = (
            "Summary\n"
            "Experienced developer with 5 years.\n\n"
            "Experience\n"
            "Software Engineer at Acme Corp.\n\n"
            "Education\n"
            "BS Computer Science, MIT.\n\n"
            "Skills\n"
            "Python, FastAPI, Docker.\n"
        )
        sections = service.parse_sections(raw)
        types = [s[0] for s in sections]
        assert SectionType.SUMMARY in types
        assert SectionType.EXPERIENCE in types
        assert SectionType.EDUCATION in types
        assert SectionType.SKILLS in types

    def test_no_headings_returns_summary(self) -> None:
        """Text with no recognized headings returns as SUMMARY."""
        service = ResumeParsingDomainService()
        raw = "Just some plain text without headings."
        sections = service.parse_sections(raw)
        assert len(sections) == 1
        assert sections[0][0] == SectionType.SUMMARY


class TestResumeFactory:
    """Tests for ResumeFactory."""

    def test_creates_resume_with_sections(self) -> None:
        """Factory should create Resume with parsed sections."""
        service = ResumeParsingDomainService()
        raw = "Summary\nA great developer.\n\nSkills\nPython, TypeScript.\n"
        resume = ResumeFactory.create_from_upload(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            filename="test.pdf",
            storage_path="t/u/test.pdf",
            raw_text=raw,
            parsing_service=service,
        )
        assert isinstance(resume, Resume)
        assert resume.filename == "test.pdf"
        assert resume.section_count >= 1
        assert resume.parsed_data is not None


class TestResumeEntity:
    """Tests for Resume aggregate root."""

    def test_add_section(self) -> None:
        """add_section should append to sections list."""
        resume = Resume(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            filename="test.pdf",
            storage_path="path",
        )
        section = ResumeSection(
            resume_id=resume.id,
            section_type=SectionType.SKILLS,
            content="Python, Go",
            order_index=0,
        )
        resume.add_section(section)
        assert resume.section_count == 1
        assert resume.sections[0].section_type == SectionType.SKILLS


class TestPDFParser:
    """Tests for PDFParser adapter."""

    def test_extracts_text_from_pdf(self) -> None:
        """PDFParser should extract text from valid PDF bytes."""
        parser = PDFParser()
        pdf_bytes = _make_test_pdf("Hello World Resume")
        text = parser.extract_text(pdf_bytes)
        assert isinstance(text, str)

    def test_invalid_pdf_raises(self) -> None:
        """PDFParser should raise ValueError for non-PDF bytes."""
        parser = PDFParser()
        with pytest.raises(ValueError, match="Failed to parse"):
            parser.extract_text(b"not a pdf file")


# ===================================================================
# API Integration Tests (with mocked file storage)
# ===================================================================
@pytest.fixture
async def resume_test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Test client with mocked FileStorageAdapter."""
    from main import app
    from resume.api.routes import get_resume_service
    from shared.infrastructure.database import get_async_session

    # Override DB session
    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = _override_session

    # Override resume service to use mock storage
    mock_storage = _mock_file_storage()

    async def _override_resume_service() -> ResumeApplicationService:
        return ResumeApplicationService(
            repo=ResumeRepository(db_session),
            file_storage=mock_storage,
            pdf_parser=PDFParser(),
            parsing_service=ResumeParsingDomainService(),
            vector_store=VectorStoreAdapter(),
            uow=SqlAlchemyUnitOfWork(db_session),
        )

    app.dependency_overrides[get_resume_service] = _override_resume_service

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestResumeAPI:
    """Integration tests for resume API endpoints."""

    @pytest.mark.asyncio
    async def test_upload_pdf_returns_201(
        self, resume_test_client: AsyncClient
    ) -> None:
        """POST /api/resumes/upload with valid PDF returns 201."""
        reg = await resume_test_client.post(
            "/api/auth/register",
            json={
                "email": "resume-up@example.com",
                "password": "Password123",
                "tenant_name": "Resume Upload Corp",
            },
        )
        token = reg.json()["access_token"]

        pdf_bytes = _make_test_pdf("Test Resume")
        resp = await resume_test_client.post(
            "/api/resumes/upload",
            files={
                "file": (
                    "resume.pdf",
                    io.BytesIO(pdf_bytes),
                    "application/pdf",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["filename"] == "resume.pdf"

    @pytest.mark.asyncio
    async def test_list_resumes_returns_200(
        self, resume_test_client: AsyncClient
    ) -> None:
        """GET /api/resumes/ returns 200 with list."""
        reg = await resume_test_client.post(
            "/api/auth/register",
            json={
                "email": "resume-ls@example.com",
                "password": "Password123",
                "tenant_name": "List Corp",
            },
        )
        token = reg.json()["access_token"]

        resp = await resume_test_client.get(
            "/api/resumes/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_upload_non_pdf_returns_400(
        self, resume_test_client: AsyncClient
    ) -> None:
        """POST /api/resumes/upload with non-PDF returns 400."""
        reg = await resume_test_client.post(
            "/api/auth/register",
            json={
                "email": "resume-bad@example.com",
                "password": "Password123",
                "tenant_name": "Bad Corp",
            },
        )
        token = reg.json()["access_token"]

        resp = await resume_test_client.post(
            "/api/resumes/upload",
            files={
                "file": (
                    "notes.txt",
                    io.BytesIO(b"plain text"),
                    "text/plain",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_without_token_returns_401(
        self, resume_test_client: AsyncClient
    ) -> None:
        """POST /api/resumes/upload without token returns 401."""
        pdf_bytes = _make_test_pdf("No auth")
        resp = await resume_test_client.post(
            "/api/resumes/upload",
            files={
                "file": (
                    "resume.pdf",
                    io.BytesIO(pdf_bytes),
                    "application/pdf",
                )
            },
        )
        assert resp.status_code == 401
