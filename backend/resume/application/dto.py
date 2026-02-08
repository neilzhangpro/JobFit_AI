"""DTOs for the Resume bounded context.

Data Transfer Objects for API request/response serialization.
"""

from datetime import datetime

from pydantic import BaseModel


class ResumeSectionDTO(BaseModel):
    """Public representation of a resume section."""

    id: str
    section_type: str
    content: str
    order_index: int


class ResumeDetailDTO(BaseModel):
    """Full resume detail with all sections."""

    id: str
    filename: str
    storage_path: str
    sections: list[ResumeSectionDTO]
    created_at: datetime


class ResumeListItemDTO(BaseModel):
    """Lightweight resume item for list views."""

    id: str
    filename: str
    section_count: int
    created_at: datetime


class UploadResumeResponse(BaseModel):
    """Response after successful resume upload."""

    id: str
    filename: str
    section_count: int
    message: str
