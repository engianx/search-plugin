"""Product-related utility functions."""
from urllib.parse import urlparse

def get_product_handle(url: str) -> str:
    """Extract product handle from URL.

    Args:
        url: Product page URL

    Returns:
        str: Product handle (last part of URL path)
    """
    path = urlparse(url).path
    return path.strip('/').split('/')[-1]