"""ResumeParsingDomainService — splits raw text into sections.

Pure domain logic with no external dependencies. Uses keyword
matching to identify common resume section headings.
"""

import re

from resume.domain.value_objects import SectionType

# Map heading keywords to SectionType values
_HEADING_MAP: dict[str, SectionType] = {
    "education": SectionType.EDUCATION,
    "academic": SectionType.EDUCATION,
    "experience": SectionType.EXPERIENCE,
    "work experience": SectionType.EXPERIENCE,
    "employment": SectionType.EXPERIENCE,
    "professional experience": SectionType.EXPERIENCE,
    "projects": SectionType.PROJECTS,
    "project": SectionType.PROJECTS,
    "skills": SectionType.SKILLS,
    "technical skills": SectionType.SKILLS,
    "core competencies": SectionType.SKILLS,
    "certifications": SectionType.CERTIFICATIONS,
    "certificates": SectionType.CERTIFICATIONS,
    "licenses": SectionType.CERTIFICATIONS,
    "summary": SectionType.SUMMARY,
    "professional summary": SectionType.SUMMARY,
    "objective": SectionType.SUMMARY,
    "profile": SectionType.SUMMARY,
    "about me": SectionType.SUMMARY,
}

# Regex: line that looks like a section heading
_HEADING_PATTERN = re.compile(
    r"^[\s]*(" + "|".join(re.escape(k) for k in _HEADING_MAP) + r")[\s]*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class ResumeParsingDomainService:
    """Splits raw resume text into typed sections.

    Uses keyword matching against common resume headings
    to identify section boundaries.
    """

    def parse_sections(self, raw_text: str) -> list[tuple[SectionType, str]]:
        """Parse raw text into a list of (SectionType, content).

        Args:
            raw_text: The full extracted text from the PDF.

        Returns:
            A list of tuples, each containing the section type
            and the text content of that section. If no headings
            are found, returns the entire text as SUMMARY.
        """
        matches = list(_HEADING_PATTERN.finditer(raw_text))

        if not matches:
            # No recognized headings — treat as single summary
            return [(SectionType.SUMMARY, raw_text.strip())]

        sections: list[tuple[SectionType, str]] = []

        for i, match in enumerate(matches):
            heading_text = match.group(1).strip().lower()
            section_type = _HEADING_MAP.get(heading_text, SectionType.SUMMARY)

            # Content runs from end of heading to start of next
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            content = raw_text[start:end].strip()

            if content:
                sections.append((section_type, content))

        return sections
