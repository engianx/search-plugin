"""Tests for sitemap crawler."""
import unittest
from search.sitemap.crawler import WebsiteSitemapSpider

class TestWebsiteSitemapSpider(unittest.TestCase):
    """Test cases for WebsiteSitemapSpider."""

    def setUp(self):
        """Set up test fixtures."""
        self.spider = WebsiteSitemapSpider(url='https://example.com', output_dir='/tmp/test')

    def test_get_local_path(self):
        """Test local path generation for different URL patterns."""
        test_cases = [
            # Basic paths
            {
                'url': 'https://dodoutdoors.com/products/tent',
                'expected': 'html/products/tent'
            },
            # Path with existing extension
            {
                'url': 'https://dodoutdoors.com/docs/manual.pdf',
                'expected': 'html/docs/manual.pdf'
            },
            # Root path
            {
                'url': 'https://dodoutdoors.com/',
                'expected': 'html/index.html'
            },
            # Deep nested path
            {
                'url': 'https://dodoutdoors.com/pt/pages/central-oregon-sportsmans',
                'expected': 'html/pt/pages/central-oregon-sportsmans'
            },
            # Path with query parameters (should ignore them)
            {
                'url': 'https://dodoutdoors.com/products/tent?color=red',
                'expected': 'html/products/tent'
            },
            # Path with fragments (should ignore them)
            {
                'url': 'https://dodoutdoors.com/about#contact',
                'expected': 'html/about'
            },
            # Path ending with slash
            {
                'url': 'https://dodoutdoors.com/products/',
                'expected': 'html/products/index.html'
            }
        ]

        for test_case in test_cases:
            with self.subTest(url=test_case['url']):
                result = self.spider._get_local_path(test_case['url'])
                self.assertEqual(
                    result,
                    test_case['expected'],
                    f"For URL {test_case['url']}, expected {test_case['expected']}, but got {result}"
                )

if __name__ == '__main__':
    unittest.main()