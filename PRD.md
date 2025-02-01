# Website Scraper Project Requirements

## Overview
A website scraper that extracts and processes content from websites, handling both product pages and general content pages. The system consists of three main components: sitemap crawler, page crawler, and content processor.

## Components

### 1. Sitemap Crawler
- **Input**:
  - Website URL
  - Data directory path

- **Functionality**:
  - Parse robots.txt to find XML sitemaps
  - Handle nested sitemap files
  - Extract all URLs and their metadata

- **Output**: JSON file containing URL metadata
  - URL
  - Last modified date (from sitemap)
  - Priority (from sitemap)
  - Crawl status (not crawled, success, failed)
  - Crawl timestamp
  - Page type (product/document)
  - Error messages (if any)
  - Local file path (for crawled content)

### 2. Page Crawler
- **Configuration** (YAML file with CLI override support):
  - Request timeout
  - Delay between requests (rate limiting)
  - Maximum retries per URL
  - Concurrent requests limit
  - Custom headers
  - Cookie handling
  - JavaScript rendering timeout
  - Proxy service settings

- **Features**:
  - Support for multiple proxy services (zenrows, etc.)
  - Anti-bot handling
  - JavaScript rendering support

- **Output**:
  - Raw HTML content saved in 'html' subdirectory
  - Updated metadata JSON with crawl status

### 3. Content Processor
- **Product Pages** (URLs starting with '/products/'):
  - Use provided JSON schema (fixed per website)
  - Extract structured data using LLM
  - Fields are optional, not exhaustive
  - Preserve additional important information from LLM
  - Support multiple LLM providers
  - Save as JSON in 'products' subdirectory

- **Other Pages**:
  - Extract and store in JSON format:
    * URL
    * Title
    * Clean content (headers/footers removed)
  - Save in 'documents' subdirectory

## Directory Structure
data/
├── metadata.json # URL metadata
├── html/ # Raw HTML files
├── products/ # Processed product JSONs
└── documents/ # Processed document JSONs

## Technical Requirements
- Support for multiple LLM providers
- YAML configuration with command-line override support
- Error handling and logging
- Default to OpenAI's GPT-4-turbo model for LLM processing


Here's a proposed source file structure for the entire project:

website_scraper/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   └── default.yaml       # Default configuration
├── src/
│   └── search/
│       ├── __init__.py
│       ├── cli.py         # Command line interface
│       ├── sitemap/
│       │   ├── __init__.py
│       │   └── crawler.py # Our sitemap crawler implementation
│       ├── page/
│       │   ├── __init__.py
│       │   └── crawler.py # Page crawler with proxy support
│       ├── processor/
│       │   ├── __init__.py
│       │   ├── base.py    # Base processor
│       │   ├── product.py # Product page processor
│       │   └── document.py# Document page processor
│       └── utils/
│           ├── __init__.py
│           ├── config.py  # Configuration handling
│           └── storage.py # File storage utilities
└── tests/
    └── search/
        ├── __init__.py
        ├── sitemap/
        ├── page/
        └── processor/