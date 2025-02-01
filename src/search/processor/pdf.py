"""PDF document processor."""
import logging
from typing import Dict, Any
import pdfplumber
import re

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean extracted text content.

    Args:
        text: Raw text content

    Returns:
        str: Cleaned text with normalized whitespace
    """
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_title(pdf) -> str:
    """Extract title from PDF metadata or first page.

    Args:
        pdf: PDFPlumber object

    Returns:
        str: Extracted title or empty string if not found
    """
    # Try to get title from PDF metadata
    if pdf.metadata:
        # Check different possible metadata keys for title
        for key in ['/Title', 'title', 'Title']:
            if key in pdf.metadata and pdf.metadata[key]:
                return clean_text(pdf.metadata[key])

    # Fallback: try to find title in first page
    if len(pdf.pages) > 0:
        first_page = pdf.pages[0]
        first_text = first_page.extract_text()
        if first_text:
            # Take first non-empty line as title
            lines = [line.strip() for line in first_text.split('\n') if line.strip()]
            if lines:
                return lines[0]

    return ''

def process_pdf(file_path: str) -> Dict[str, Any]:
    """Process PDF file and extract structured data.

    Args:
        file_path: Path to PDF file

    Returns:
        dict: Extracted data with fields:
            - title: str, document title
            - content: str, main text content

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If PDF processing fails
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract title
            title = extract_title(pdf)

            # Extract content from all pages
            content_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content_parts.append(clean_text(text))

            content = ' '.join(content_parts)

            # Log metadata for debugging
            logger.debug(f"PDF metadata: {pdf.metadata}")
            logger.debug(f"Extracted title: {title}")

            return {
                'title': title,
                'content': content
            }

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to process PDF file {file_path}: {str(e)}")
        raise ValueError(f"PDF processing failed: {str(e)}")