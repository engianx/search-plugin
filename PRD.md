# Semantic Search Plugin Project Requirements

## Overview
A semantic search plugin that enables natural language search capabilities for e-commerce websites. The system consists of four main components: sitemap crawler, page crawler, content processor, and a user interface with API server.

## Components

### 1. Backend Components (@search)

#### 1.1 Sitemap Crawler
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

#### 1.2 Page Crawler
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

#### 1.3 Content Processor
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

### 2. Frontend Components (@ui)
- **Search Dialog**:
  - Floating search button
  - Expandable search input
  - Results display with product cards
  - Image carousel for product images
  - Answer section for non-product queries

- **Demo Page**:
  - Website preview iframe
  - Integrated search dialog
  - Domain-specific routing

### 3. API Server (@api)
- **Search Endpoint**:
  - Natural language query processing
  - Product and content search
  - Relevance ranking
  - Response formatting

- **Proxy Endpoint**:
  - Website preview functionality
  - Security header handling
  - CORS support

## Directory Structure

project/
├── search/ # Backend crawler and processor
│ ├── sitemap/
│ ├── page/
│ └── processor/
├── api/ # API and proxy servers
│ ├── search/
│ └── proxy/
├── ui/ # Frontend components
│ ├── src/
│ │ ├── components/
│ │ └── pages/
│ └── public/
└── data/ # Processed data
├── metadata.json
├── html/
├── products/
└── documents/