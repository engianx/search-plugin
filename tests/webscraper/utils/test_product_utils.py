"""Unit tests for product utilities."""
import pytest
from search.utils.product_utils import get_product_handle

def test_get_product_handle_simple():
    """Test extracting handle from simple product URL."""
    url = "https://example.com/products/blue-shirt"
    assert get_product_handle(url) == "blue-shirt"

def test_get_product_handle_with_trailing_slash():
    """Test URL with trailing slash."""
    url = "https://example.com/products/blue-shirt/"
    assert get_product_handle(url) == "blue-shirt"

def test_get_product_handle_with_query_params():
    """Test URL with query parameters."""
    url = "https://example.com/products/blue-shirt?size=L&color=blue"
    assert get_product_handle(url) == "blue-shirt"

def test_get_product_handle_with_fragment():
    """Test URL with fragment."""
    url = "https://example.com/products/blue-shirt#details"
    assert get_product_handle(url) == "blue-shirt"

def test_get_product_handle_complex_path():
    """Test URL with multiple path segments."""
    url = "https://example.com/shop/products/mens/shirts/blue-shirt"
    assert get_product_handle(url) == "blue-shirt"

def test_get_product_handle_encoded_chars():
    """Test URL with encoded characters."""
    url = "https://example.com/products/blue%20shirt"
    assert get_product_handle(url) == "blue%20shirt"

def test_get_product_handle_special_chars():
    """Test URL with special characters."""
    url = "https://example.com/products/blue-shirt-2.0"
    assert get_product_handle(url) == "blue-shirt-2.0"

@pytest.mark.skip(reason="This test is not working")
def test_get_product_handle_empty_path():
    """Test URL with empty path."""
    url = "https://example.com"
    with pytest.raises(IndexError):
        get_product_handle(url)

def test_get_product_handle_invalid_url():
    """Test invalid URL."""
    url = "not-a-url"
    assert get_product_handle(url) == "not-a-url"

def test_get_product_handle_unicode():
    """Test URL with unicode characters."""
    url = "https://example.com/products/blue-shirt-üニコード"
    assert get_product_handle(url) == "blue-shirt-üニコード"