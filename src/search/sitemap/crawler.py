"""Sitemap crawler implementation."""
import os
import logging
from typing import Any, Iterator
from datetime import datetime
from scrapy.spiders import SitemapSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..utils.storage import save_metadata, save_stats
from ..utils.config import load_config
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebsiteSitemapSpider(SitemapSpider):
    name = 'sitemap_spider'

    def __init__(self, url=None, site_dir=None, config=None, *args, **kwargs):
        logger.info(f"Initializing spider for {url}")
        # Initialize base URL and output directory
        self.base_url = url
        self.site_dir = site_dir

        domain = urlparse(url).netloc
        # Parse the base URL
        self.allowed_domains = [domain]

        # Find sitemap URL from robots.txt
        self.sitemap_urls = [f'{url}/robots.txt']

        # Set sitemap_follow from config if it exists, otherwise use default which is [""]
        self.sitemap_follow = config.get('sitemap_follow', self.sitemap_follow)
        logger.info(f"Using sitemap_follow patterns: {self.sitemap_follow}")

        super().__init__(*args, **kwargs)

        # Initialize metadata storage
        self.metadata = {}
        self.metadata_file = os.path.join(site_dir, 'sitemap_metadata.json')
        self.stats_file = os.path.join(site_dir, 'sitemap_stats.json')

        # Initialize stats with simpler structure
        self.stats = {
            'total_urls': 0,
            'product_urls': 0,
            'document_urls': 0,
            'total_images': 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': None
        }

    # These functions overwrite Sitemap.__iter__ so that it can handle nested entries such as:
    # <url>
    #   <loc>https://dodoutdoors.com/products/sugoi-chair</loc>
    #   <lastmod>2025-01-29T13:04:46-08:00</lastmod>
    #   <changefreq>daily</changefreq>
    #   <image:image>
    #       <image:loc>https://cdn.shopify.com/s/files/1/0555/1154/8056/files/1_GIFSUGOITANDEFAULTCopyofGIF8-Versamin2.gif?v=1724230329</image:loc>
    #       <image:title>Sugoi Chair</image:title>
    #       <image:caption>both</image:caption>
    #   </image:image>
    # </url>

    def _extract(self, elem) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for el in elem.getchildren():
            tag = el.tag
            assert isinstance(tag, str)
            name = tag.split("}", 1)[1] if "}" in tag else tag

            if name == "link":
                if "href" in el.attrib:
                    d.setdefault("alternate", []).append(el.get("href"))
            else:
                if el.text and el.text.strip():
                    d[name] = el.text.strip()
                else:
                    d[name] = self._extract(el)
        return d

    def _iterate(self, root) -> Iterator[dict[str, Any]]:
        for elem in root.getchildren():
            d = self._extract(elem)
            if "loc" in d:
                yield d

    def sitemap_filter(self, sitemap):
        """Filter sitemap entries and create initial metadata."""
        logger.info("Processing sitemap entries")

        if sitemap.type == "sitemapindex":
            for entry in sitemap:
                yield entry

            return

        # urlset
        for entry in self._iterate(sitemap._root):
            url = entry['loc']

            # Determine page type
            is_product = '/products/' in url
            page_type = 'product' if is_product else 'document'

            # Create metadata for each content URL
            metadata = {
                'last_modified': entry.get('lastmod', None),
                'priority': entry.get('priority', None),
                'changefreq': entry.get('changefreq', None),
                'page_type': page_type,
                'local_file': self._get_local_path(url),
                'image': entry.get('image', None)
            }

            self.metadata[url] = metadata

            # Update stats
            self.stats['total_urls'] += 1
            if is_product:
                self.stats['product_urls'] += 1
            else:
                self.stats['document_urls'] += 1
            if metadata['image']:
                self.stats['total_images'] += len(metadata['image'])

    def _get_local_path(self, url):
        """Generate local file path for URL content."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # Handle empty path or path ending with slash
        if not path:
            return 'html/index.html'

        # Split path into parts
        path_parts = path.split('/')

        # If the path ends with a slash, add index.html
        if parsed.path.endswith('/'):
            return os.path.join('html', *path_parts, 'index.html')

        return os.path.join('html', *path_parts)

    def closed(self, reason):
        """Save metadata and stats when spider closes."""
        # Update final stats
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['duration_seconds'] = (
            datetime.fromisoformat(self.stats['end_time']) -
            datetime.fromisoformat(self.stats['start_time'])
        ).total_seconds()

        logger.info(f"Spider closing. Reason: {reason}")
        logger.info(f"Found {len(self.metadata)} URLs")
        logger.info(f"Stats: {self.stats}")

        # Save metadata and stats
        save_metadata(self.metadata, self.metadata_file)
        save_stats(self.stats, self.stats_file)

    def parse(self, response):
        """Parse each URL from sitemap."""
        # This method is called for each URL in the sitemap
        # We don't need to do anything here as we're just collecting URLs
        # Create metadata for each URL
        pass


def run_spider(url, site_dir):
    """Helper function to run the spider programmatically."""
    logger.info(f"Setting up sitemap crawler for: {site_dir}")

    domain = urlparse(url).netloc

    # Load domain-specific config,
    config = load_config(domain)

    process = CrawlerProcess(get_project_settings())
    process.crawl(WebsiteSitemapSpider,
                 url=url,
                 site_dir=site_dir,
                 config=config)
    process.start()
