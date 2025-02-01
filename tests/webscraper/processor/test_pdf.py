"""Tests for PDF processor."""
import os
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from search.processor.pdf import process_pdf, clean_text

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def create_test_pdf(filename: str, pages: list[str], metadata: dict = None) -> str:
    """Helper function to create test PDF files."""
    test_file = os.path.join(TEST_DATA_DIR, filename)
    os.makedirs(TEST_DATA_DIR, exist_ok=True)

    # Create PDF with test content
    c = canvas.Canvas(test_file, pagesize=letter)

    # Set PDF metadata directly with reportlab
    if metadata:
        if 'title' in metadata:
            c.setTitle(metadata['title'])
        if 'author' in metadata:
            c.setAuthor(metadata['author'])
        if 'subject' in metadata:
            c.setSubject(metadata['subject'])

    # Add pages
    for page_text in pages:
        c.drawString(72, 720, page_text)
        c.showPage()

    c.save()
    return test_file

def test_clean_text():
    """Test text cleaning function."""
    # Test whitespace normalization
    assert clean_text('  hello   world  \n\t  ') == 'hello world'

    # Test empty string
    assert clean_text('') == ''

    # Test multiple spaces and newlines
    assert clean_text('hello\n\nworld\n  !') == 'hello world !'

def test_extract_title_from_metadata():
    """Test title extraction from PDF metadata."""
    test_file = create_test_pdf(
        'metadata_title.pdf',
        ['Some content'],
        metadata={'title': 'Test Document Title'}
    )

    result = process_pdf(test_file)
    assert result['title'] == 'Test Document Title'

def test_process_pdf_basic():
    """Test processing of a basic PDF file."""
    test_file = create_test_pdf(
        'basic.pdf',
        ['Page 1 content', 'Page 2 content'],
        metadata={'title': 'Test Document'}
    )

    result = process_pdf(test_file)
    assert result['title'] == 'Test Document'
    assert 'Page 1 content' in result['content']
    assert 'Page 2 content' in result['content']

def test_process_pdf_no_metadata():
    """Test processing PDF without metadata."""
    test_file = create_test_pdf(
        'no_metadata.pdf',
        ['This is page 1', 'This is page 2']
    )

    result = process_pdf(test_file)
    assert result['title'] == 'untitled'
    assert 'This is page 1' in result['content']
    assert 'This is page 2' in result['content']

def test_process_pdf_empty_pages():
    """Test processing PDF with empty pages."""
    test_file = create_test_pdf(
        'empty_pages.pdf',
        ['', 'Some content', '']
    )

    result = process_pdf(test_file)
    assert 'Some content' in result['content']

def test_process_pdf_missing_file():
    """Test handling of missing file."""
    with pytest.raises(FileNotFoundError):
        process_pdf('nonexistent.pdf')

def test_process_pdf_invalid_file():
    """Test handling of invalid PDF file."""
    test_file = os.path.join(TEST_DATA_DIR, 'invalid.pdf')
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    with open(test_file, 'w') as f:
        f.write('Not a PDF file')

    with pytest.raises(ValueError):
        process_pdf(test_file)

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test files after each test."""
    yield
    if os.path.exists(TEST_DATA_DIR):
        for file in os.listdir(TEST_DATA_DIR):
            os.remove(os.path.join(TEST_DATA_DIR, file))
        os.rmdir(TEST_DATA_DIR)