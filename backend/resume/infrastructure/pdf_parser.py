"""PDFParser — PyPDF2 adapter for text extraction (Adapter pattern).

Wraps PyPDF2 to extract raw text from uploaded PDF resumes.
Implements a parser interface to allow swapping to pdfplumber if needed (Strategy).
"""

# TODO(#60): Implement PDFParser with extract_text(file) method
# TODO(#61): Add fallback to pdfplumber for complex layouts
