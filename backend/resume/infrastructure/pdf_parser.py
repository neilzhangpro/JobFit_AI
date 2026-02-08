"""PDFParser — PyPDF2 adapter for text extraction (Adapter pattern).

Wraps PyPDF2 to extract raw text from uploaded PDF resumes.
"""

import io
import logging

from PyPDF2 import PdfReader  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class PDFParser:
    """Extracts text from PDF file bytes using PyPDF2."""

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract all text from a PDF file.

        Args:
            file_bytes: Raw bytes of the PDF file.

        Returns:
            The concatenated text from all pages.

        Raises:
            ValueError: If the file cannot be parsed as PDF.
        """
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            result = "\n".join(pages)
            logger.info(
                "Extracted %d chars from %d pages",
                len(result),
                len(reader.pages),
            )
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}") from e
