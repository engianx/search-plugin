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
cd search-plugin

# Create a python virtual environment
python3 -m venv .venv

# Activate the environment and set correct PYTHONPATH
. ./py_env.sh

# Install dependencies
pip3 install -r requirements.txt
```

## Setup
The system requires:
1. mongodb: the simplest way to get it is to pull a pre-built docker image.
MongoDB is used for cache LLM calls, such as embedding and offline document process.

2. elasticsearch: use docker image is also the easiest way.
ElasticSearch is used to build the search index, we use the dense vector
for semantic search.

Update `config/default.yaml` if they are running on different servers:
```yaml
mongodb:
  uri: "mongodb://localhost:27017"
  test_uri: "mongodb://localhost:27017"

elasticsearch:
  uri: "http://localhost:9200"
  test_uri: "http://localhost:9200"
```

## Usage

### Crawling and Processing
```bash
cd src/
# Step 1: Crawl sitemap
python3 -m search.cli sitemap https://dodoutdoors.com $HOME/data
# Check the sitemap info $HOME/data/dodoutdoors.com
# sitemap_metadata.json and sitemap_stats.json

# Step 2: Crawl pages (without proxy)
python3 -m search.cli pages https://dodoutdoors.com $HOME/data
# Check crawled pages under $HOME/data/dodoutdoors.com
# pages_metadata.json and pages_stats.json

# Step 3.1: Process crawled pages
python3 -m search.cli process https://dodoutdoors.com $HOME/data --workers 4
# Step 3.2: Extract product data
python3 -m search.cli products https://dodoutdoors.com $HOME/data
# Step 3.3: Generate Q&A from pages
python3 -m search.cli qa https://dodoutdoors.com $HOME/data

# Step 4.1: Build the index
python3 -m search.cli index https://dodoutdoors.com $HOME/data
# Step 4.2: Index Q&A data
python3 -m search.cli index-qa https://dodoutdoors.com $HOME/data
```

### Serving the API and Demo UI
```bash
# Run the API server (which includes the proxy endpoint)
python3 -m search.api.server

# Query the API:
curl "http://localhost:8080/search/dodoutdoors.com?query=your+search+query"
```

### Demo UI
The UI is built with Vite/React. To run the demo:
```bash
cd ui/
npm install
npm run dev -- --host 0.0.0.0
```
Then, open your browser at http://localhost:5173. Visit a demo URL, for example:
`http://localhost:5173/demo/dodoutdoors.com`
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
pytest tests
```