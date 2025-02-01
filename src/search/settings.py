"""Scrapy settings for search-plugin project."""

CONCURRENT_REQUESTS = 32

# Basic crawler settings
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 1.0
RETRY_TIMES = 3
CONCURRENT_REQUESTS = 5

# Optional proxy middleware settings
ZENROWS_API_KEY = '1234567890'  # Set this via environment variable
DOWNLOADER_MIDDLEWARES = {
    # Uncomment to enable ZenRows proxy
    # 'scrapy_zenrows.ZenRowsMiddleware': 100,
}

# Other Scrapy settings
ROBOTSTXT_OBEY = True
LOG_LEVEL = 'INFO'
