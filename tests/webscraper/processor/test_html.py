"""Tests for HTML processor."""
import os
import pytest
from search.processor.html import process_html, clean_text

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_clean_text():
    """Test text cleaning function."""
    # Test whitespace normalization
    assert clean_text('  hello   world  \n\t  ') == 'hello world'

    # Test empty string
    assert clean_text('') == ''

    # Test multiple spaces and newlines
    assert clean_text('hello\n\nworld\n  !') == 'hello world !'

def test_process_html_basic():
    """Test processing of a basic HTML file."""
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <main>
                <h1>Welcome</h1>
                <p>This is the main content.</p>
            </main>
        </body>
    </html>
    """
    test_file = os.path.join(TEST_DATA_DIR, 'basic.html')
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    result = process_html(test_file)
    assert result['title'] == 'Test Page'
    assert 'main content' in result['content']
    assert 'Welcome' in result['content']

def test_process_html_with_unwanted_elements():
    """Test removal of unwanted elements."""
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
            <style>
                body { color: black; }
            </style>
            <script>
                console.log('test');
            </script>
        </head>
        <body>
            <header>Site Header</header>
            <nav>Navigation</nav>
            <main>
                <p>Main content here.</p>
            </main>
            <footer>Site Footer</footer>
        </body>
    </html>
    """
    test_file = os.path.join(TEST_DATA_DIR, 'with_unwanted.html')
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    result = process_html(test_file)
    assert 'Main content here' in result['content']
    assert 'Site Header' not in result['content']
    assert 'Navigation' not in result['content']
    assert 'Site Footer' not in result['content']

def test_process_html_fallback():
    """Test fallback to body when no main content container found."""
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <div>
                <p>Some content without main tag.</p>
            </div>
        </body>
    </html>
    """
    test_file = os.path.join(TEST_DATA_DIR, 'no_main.html')
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    result = process_html(test_file)
    assert 'content without main tag' in result['content']

def test_process_html_missing_file():
    """Test handling of missing file."""
    with pytest.raises(FileNotFoundError):
        process_html('nonexistent.html')

def test_process_html_invalid_content():
    """Test handling of invalid HTML content."""
    html_content = "Not valid HTML"
    test_file = os.path.join(TEST_DATA_DIR, 'invalid.html')
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    result = process_html(test_file)
    assert result['title'] == ''
    assert 'Not valid HTML' in result['content']

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test files after each test."""
    yield
    if os.path.exists(TEST_DATA_DIR):
        for file in os.listdir(TEST_DATA_DIR):
            os.remove(os.path.join(TEST_DATA_DIR, file))
        os.rmdir(TEST_DATA_DIR)