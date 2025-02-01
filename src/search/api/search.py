"""Search API implementation."""
import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..utils.config import load_config
from ..utils.embeddings import EmbeddingsGenerator
from .formatter import SearchResultFormatter
from .proxy import proxy_request

logger = logging.getLogger(__name__)

app = FastAPI(title="Webscraper Search API")

# Configure CORS with sensible defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],
)

class ProductResult(BaseModel):
    """Product search result."""
    url: str
    title: str
    price: float
    images: List[str]
    highlights: List[str]

class Answer(BaseModel):
    """Document answer."""
    url: str
    content: str

class SearchResponse(BaseModel):
    """Search response model."""
    products: List[ProductResult]
    answer: Optional[Answer]

@app.get("/search/{domain}", response_model=SearchResponse)
async def search(domain: str, query: str, limit: int = 20) -> SearchResponse:
    """Search documents in domain index.

    Args:
        domain: Domain name (index to search)
        query: Search query text
        limit: Maximum number of results to return

    Returns:
        SearchResponse containing products and answer
    """
    try:
        # Initialize elasticsearch client
        config = load_config(domain)
        es = Elasticsearch(config["elasticsearch"]["uri"])

        # Check if index exists
        if not es.indices.exists(index=domain):
            raise HTTPException(
                status_code=404,
                detail=f"Index not found for domain: {domain}"
            )

        # Generate query embedding
        embeddings = EmbeddingsGenerator()
        query_vector = embeddings.generate_single(query)

        # Construct search query
        search_query = {
            "knn": {
                "field": "chunks.vector",
                "query_vector": query_vector.tolist(),
                "k": limit,
                "num_candidates": limit * 2
            },
            "_source": ["title", "url", "chunks.content", "chunks.chunk_type", "chunks.metadata"]
        }

        # Execute search
        response = es.search(
            index=domain,
            body=search_query,
            size=limit
        )

        # Process raw results
        raw_results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            # Find the matching chunk (the one with highest score)
            matching_chunk = source["chunks"][0]  # First chunk is the matching one due to knn search

            raw_results.append({
                "title": source["title"],
                "url": source["url"],
                "content": matching_chunk["content"],
                "chunk_type": matching_chunk["chunk_type"],
                "metadata": matching_chunk.get("metadata", {}),
                "score": hit["_score"]
            })

        # Format results using the formatter
        data_dir = config.get('data_dir')
        if not data_dir:
            raise HTTPException(
                status_code=500,
                detail="data_dir not found in configuration"
            )

        site_dir = os.path.join(data_dir, domain)
        formatter = SearchResultFormatter(site_dir, config)

        formatted_results = formatter.format_results(raw_results)

        return SearchResponse(**formatted_results)

    except FileNotFoundError as e:
        logger.error(f"Metadata error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Site metadata not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/proxy")
async def proxy(url: str):
    """Proxy endpoint to handle X-Frame-Options."""
    return await proxy_request(url)