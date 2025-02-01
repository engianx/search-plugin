"""Tests for search API."""
import pytest
from fastapi.testclient import TestClient
import numpy as np
from unittest.mock import Mock, patch
from search.api.search import app
from search.utils.embeddings import EmbeddingsGenerator

client = TestClient(app)

def test_search_invalid_domain():
    """Test search with non-existent domain."""
    response = client.get("/search/invalid-domain", params={"query": "test"})
    assert response.status_code == 404
    assert "Index not found" in response.json()["detail"]

@patch("search.api.search.Elasticsearch")
@patch("search.api.search.EmbeddingsGenerator")
def test_search_success(mock_embeddings, mock_es):
    """Test successful search."""
    # Mock embeddings
    mock_generator = Mock(spec=EmbeddingsGenerator)
    mock_generator.generate_single.return_value = np.array([1.0] * 1536)
    mock_embeddings.return_value = mock_generator

    # Mock elasticsearch response
    mock_es_instance = Mock()
    mock_es_instance.indices.exists.return_value = True
    mock_es_instance.search.return_value = {
        "took": 5,
        "hits": {
            "total": {"value": 1},
            "hits": [{
                "_score": 0.9,
                "_source": {
                    "title": "Test Document",
                    "url": "http://test.com/doc1",
                    "chunks": [{"content": "Test content"}]
                }
            }]
        }
    }
    mock_es.return_value = mock_es_instance

    # Test API
    response = client.get("/search/test-domain", params={"query": "test query"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Test Document"
    assert data["total"] == 1

@patch("search.api.search.Elasticsearch")
@patch("search.api.search.EmbeddingsGenerator")
def test_search_embeddings_error(mock_embeddings, mock_es):
    """Test search with embeddings error."""
    # Mock elasticsearch index check
    mock_es_instance = Mock()
    mock_es_instance.indices.exists.return_value = True
    mock_es.return_value = mock_es_instance

    # Mock embeddings error
    mock_generator = Mock(spec=EmbeddingsGenerator)
    mock_generator.generate_single.side_effect = Exception("API Error")
    mock_embeddings.return_value = mock_generator

    response = client.get("/search/test-domain", params={"query": "test"})
    assert response.status_code == 500
    assert "Search failed" in response.json()["detail"]