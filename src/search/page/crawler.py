"""Page crawler implementation."""
import os
import logging
from datetime import datetime
from scrapy import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..utils.storage import load_metadata, save_metadata, save_stats

logger = logging.getLogger(__name__)

class WebsitePageSpider(Spider):
    name = 'page_spider'

    def __init__(self, site_dir=None, *args, **kwargs):
        logger.info(f"Initializing page spider for: {site_dir}")
        super().__init__(*args, **kwargs)

        # Initialize paths
        self.site_dir = site_dir
        self.sitemap_metadata_file = os.path.join(site_dir, 'sitemap_metadata.json')
        self.pages_metadata_file = os.path.join(site_dir, 'pages_metadata.json')
        self.pages_stats_file = os.path.join(site_dir, 'pages_stats.json')

        # Load sitemap metadata and initialize pages metadata
        self.sitemap_metadata = load_metadata(self.sitemap_metadata_file)
        self.pages_metadata = {}
        self.start_urls = list(self.sitemap_metadata.keys())

        # Initialize stats
        self.stats = {
            'total_crawled': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_bytes': 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': None
        }

    def parse(self, response):
        """Process each downloaded page."""
        # Get original URL from request
        original_url = response.request.url
        sitemap_meta = self.sitemap_metadata[original_url]

        try:
            # Create directory if needed
            output_path = os.path.join(self.site_dir, sitemap_meta['local_file'])
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save the page content
            with open(output_path, 'wb') as f:
                f.write(response.body)

            # Create page metadata
            self.pages_metadata[original_url] = {
                'local_file': sitemap_meta['local_file'],
                'page_type': sitemap_meta['page_type'],
                'title': sitemap_meta.get('title', ''),
                'crawl_status': 'success',
                'crawl_timestamp': datetime.now().isoformat(),
                'content_size': len(response.body),
                'error_messages': []
            }

            # Add redirected URL if different
            if response.url != original_url:
                self.pages_metadata[original_url]['redirected_url'] = response.url

            # Update stats
            self.stats['successful'] += 1
            self.stats['total_bytes'] += len(response.body)

        except Exception as e:
            logger.error(f"Failed to save {original_url}: {str(e)}")
            self.pages_metadata[original_url] = {
                'local_file': sitemap_meta['local_file'],
                'page_type': sitemap_meta['page_type'],
                'crawl_status': 'failed',
                'crawl_timestamp': datetime.now().isoformat(),
                'error_messages': [str(e)]
            }
            self.stats['failed'] += 1

        finally:
            self.stats['total_crawled'] += 1

    def closed(self, reason):
        """Save metadata and stats when spider closes."""
        # Update final stats
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['duration_seconds'] = (
            datetime.fromisoformat(self.stats['end_time']) -
            datetime.fromisoformat(self.stats['start_time'])
        ).total_seconds()

        logger.info(f"Spider closing. Reason: {reason}")
        logger.info(f"Crawled {self.stats['total_crawled']} pages")
        logger.info(f"Success: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")

        # Save pages metadata and stats
        save_metadata(self.pages_metadata, self.pages_metadata_file)
        save_stats(self.stats, self.pages_stats_file)


def run_spider(site_dir, proxy_config=None):
    """Helper function to run the spider programmatically."""
    logger.info(f"Setting up page crawler for: {site_dir}")

    # Get Scrapy settings
    settings = get_project_settings()

    # Configure proxy if needed
    if proxy_config and proxy_config.get('service') == 'zenrows':
        settings.update({
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy_zenrows.ZenRowsMiddleware': 100,
            },
            'ZENROWS_API_KEY': proxy_config['api_key']
        })
        logger.info("Enabled ZenRows proxy middleware")

    # Run the spider
    process = CrawlerProcess(settings)
    process.crawl(WebsitePageSpider, site_dir=site_dir)
    process.start()
