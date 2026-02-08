"""ParsedContent and SectionType value objects for the Resume context.

Value objects are immutable and compared by value, not identity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from shared.domain.base_value_object import BaseValueObject


class SectionType(str, Enum):  # noqa: UP042
    """Resume section type — identifies the category of a section."""

    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    SUMMARY = "summary"


@dataclass(frozen=True)
class ParsedContent(BaseValueObject):
    """Immutable snapshot of a parsed resume.

    Contains both the raw extracted text and the structured
    sections as a JSON-serializable dict.
    """

    raw_text: str
    sections_json: dict[str, Any]
