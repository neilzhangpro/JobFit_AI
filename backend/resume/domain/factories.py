"""ResumeFactory — creates Resume aggregate from uploaded PDF data.

Factories encapsulate complex creation logic and ensure all
invariants are satisfied upon construction.
"""

import uuid

from resume.domain.entities import Resume, ResumeSection
from resume.domain.services import ResumeParsingDomainService
from shared.domain.domain_event import DomainEvent


class ResumeFactory:
    """Factory for creating a Resume with parsed sections."""

    @staticmethod
    def create_from_upload(
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        filename: str,
        storage_path: str,
        raw_text: str,
        parsing_service: ResumeParsingDomainService,
    ) -> Resume:
        """Create a Resume aggregate from an uploaded PDF.

        Args:
            user_id: The uploading user's UUID.
            tenant_id: The tenant UUID for data isolation.
            filename: Original filename of the uploaded PDF.
            storage_path: S3/MinIO path where the file is stored.
            raw_text: Extracted text from the PDF.
            parsing_service: Domain service to split text.

        Returns:
            A fully constructed Resume with ResumeSection entities.
        """
        # Parse text into typed sections
        parsed = parsing_service.parse_sections(raw_text)

        # Build parsed_data dict for JSON storage
        parsed_data = {
            "raw_text": raw_text,
            "sections": [
                {"type": st.value, "content": content} for st, content in parsed
            ],
        }

        resume = Resume(
            user_id=user_id,
            tenant_id=tenant_id,
            filename=filename,
            storage_path=storage_path,
            parsed_data=parsed_data,
        )

        # Create ResumeSection entities
        for i, (section_type, content) in enumerate(parsed):
            section = ResumeSection(
                resume_id=resume.id,
                section_type=section_type,
                content=content,
                order_index=i,
            )
            resume.add_section(section)

        # Publish domain event
        resume._add_event(
            DomainEvent(
                event_type="ResumeUploaded",
                payload={
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "resume_id": str(resume.id),
                },
            )
        )

        return resume
