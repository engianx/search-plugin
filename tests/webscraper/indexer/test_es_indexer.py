"""Tests for document indexer."""
import pytest
from unittest.mock import Mock, patch
import numpy as np
from search.indexer.es_indexer import DocumentIndexer
from search.utils.embeddings import EmbeddingsGenerator
from search.utils.config import load_config

# Test configuration
DOMAIN = "test-domain"
CONFIG = load_config()
ES_URI = CONFIG["elasticsearch"]["test_uri"]

@pytest.fixture
def mock_embeddings():
    """Mock embeddings generator."""
    generator = Mock(spec=EmbeddingsGenerator)
    generator.generate.return_value = np.array([[1.0] * 1536])
    return generator

@pytest.fixture
def indexer(mock_embeddings):
    """Create test indexer instance."""
    indexer = DocumentIndexer(DOMAIN, mock_embeddings)
    yield indexer

    # Cleanup
    indexer.es.indices.delete(index=DOMAIN, ignore=[404])

def test_index_creation(indexer):
    """Test index creation with mapping."""
    assert indexer.es.indices.exists(index=DOMAIN)

    mapping = indexer.es.indices.get_mapping(index=DOMAIN)[DOMAIN]["mappings"]
    assert "chunks" in mapping["properties"]
    assert mapping["properties"]["chunks"]["type"] == "nested"

def test_text_chunking(indexer):
    """Test text chunking logic."""
    text = "First sentence. Second sentence! Third sentence? Fourth sentence."
    chunks = indexer._chunk_text(text)
    assert len(chunks) > 0
    assert all(len(indexer.tokenizer.encode(chunk)) <= CONFIG["elasticsearch"]["chunk_size"]
              for chunk in chunks)

def test_document_indexing(indexer, mock_embeddings):
    """Test single document indexing."""
    doc = {
        "title": "Test Document",
        "content": "Test content with multiple sentences. Second sentence.",
        "url": "http://test.com/doc1"
    }

    result = indexer._index_document(doc)
    assert result is True

    # Verify document was indexed
    indexed_doc = indexer.es.get(index=DOMAIN, id=doc["url"])
    assert indexed_doc["_source"]["title"] == doc["title"]
    assert len(indexed_doc["_source"]["chunks"]) > 0

def test_batch_indexing(indexer):
    """Test batch document indexing."""
    docs = [
        {
            "title": f"Doc {i}",
            "content": f"Content {i}. Second sentence {i}.",
            "url": f"http://test.com/doc{i}"
        }
        for i in range(3)
    ]

    results = indexer.index_batch(docs)
    assert results["success"] == len(docs)
    assert not results["failed"]

def test_error_handling(indexer, mock_embeddings):
    """Test indexing error handling and retries."""
    mock_embeddings.generate.side_effect = Exception("API Error")

    doc = {
        "title": "Error Doc",
        "content": "Error content.",
        "url": "http://test.com/error"
    }

    with pytest.raises(Exception):
        indexer._index_document(doc)