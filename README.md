# Search Plugin

A Python-based website semantic search engine builder.

Given an e-commerce website, this tool will:
1. Scrape the site.
2. Use an LLM to extract product data and format the page content.
3. Build an index in Elasticsearch using a vector database.
4. Serve queries via an API server.

In addition, the project includes a proxy server and a user interface that can run a demo.

## Features
- Sitemap-based URL discovery and crawling
- Product data extraction using LLM
- Document content cleaning and processing for semantic search
- Indexing via Elasticsearch with vector search capabilities
- API server to query and retrieve search results
- A proxy server to bypass iframe restrictions
- A demo UI to interact with the search engine

## Installation
```bash
# Clone the repository
git clone [repository-url]
cd fast-scrape

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Crawling and Processing
```bash
cd src/
# Step 1: Crawl sitemap
python -m search.cli sitemap https://example.com $HOME/data

# Step 2: Crawl pages (without proxy)
python -m search.cli pages https://example.com $HOME/data

# Step 2: Crawl pages (with proxy)
python -m search.cli pages https://example.com $HOME/data --proxy-service zenrows --proxy-api-key YOUR_KEY

# Step 3: Process crawled pages
python -m search.cli process https://example.com $HOME/data --workers 4

# Step 4: Build the index
python -m search.cli index https://example.com $HOME/data
```

### Serving the API and Demo UI
```bash
# Run the API server (which includes the proxy endpoint)
python -m search.api.server

# Query the API:
curl "http://localhost:8080/search/example.com?query=your+search+query"
```

### Demo UI
The UI is built with Vite/React. To run the demo:
```bash
cd ui/
npm install
npm run dev
```
Then, open your browser at http://localhost:5173. Visit a demo URL, for example:
`http://localhost:5173/demo/example.com`
to see the demo with the embedded proxy.

## Configuration
Edit `config/default.yaml` to customize settings such as:
- Crawler settings
- Proxy configuration
- LLM settings
- Elasticsearch connection

## License
MIT License

## Running Tests
```bash
python -m unittest tests/search/test_sitemap/test_crawler.py
```