"""Resume (Aggregate Root) and ResumeSection (Entity).

Resume belongs to one user within a tenant.
Sections cannot exist without a resume (invariant).
"""

from __future__ import annotations

import uuid
from typing import Any

from resume.domain.value_objects import SectionType
from shared.domain.aggregate_root import AggregateRoot
from shared.domain.base_entity import BaseEntity


class ResumeSection(BaseEntity):
    """A single section of a parsed resume.

    Belongs to exactly one Resume. Cannot exist independently.
    """

    def __init__(
        self,
        resume_id: uuid.UUID,
        section_type: SectionType,
        content: str,
        order_index: int,
    ) -> None:
        super().__init__()
        self.resume_id = resume_id
        self.section_type = section_type
        self.content = content
        self.order_index = order_index


class Resume(AggregateRoot):
    """Resume aggregate root — the uploaded document and its sections.

    Manages a collection of ResumeSection entities. Sections are
    added during creation via ResumeFactory and cannot exist
    without a parent Resume.
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        filename: str,
        storage_path: str,
        parsed_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.filename = filename
        self.storage_path = storage_path
        self.parsed_data = parsed_data
        self._sections: list[ResumeSection] = []

    def add_section(self, section: ResumeSection) -> None:
        """Add a parsed section to this resume."""
        self._sections.append(section)

    @property
    def sections(self) -> list[ResumeSection]:
        """Return a copy of the internal section list."""
        return list(self._sections)

    @property
    def section_count(self) -> int:
        """Return the number of parsed sections."""
        return len(self._sections)
