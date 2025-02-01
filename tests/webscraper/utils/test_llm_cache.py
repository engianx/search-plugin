"""Tests for embeddings cache."""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch
from pymongo import MongoClient
from search.utils.llm_cache import LLMCallCache
from search.utils.config import load_config

# Test configuration
TEST_DB = "test_search"
TEST_COLLECTION = "test_embeddings_cache"
MONGO_URI = load_config()["mongodb"].get("test_uri", "mongodb://localhost:27017")

@pytest.fixture(scope="function")
def test_cache():
    """Create a test cache instance and cleanup after tests."""
    cache = LLMCallCache(
        mongodb_uri=MONGO_URI,
        database=TEST_DB,
        collection=TEST_COLLECTION
    )

    yield cache

    # Cleanup after test
    cache.clear()
    client = MongoClient(MONGO_URI)
    client.drop_database(TEST_DB)
    client.close()

def test_cache_initialization(test_cache):
    """Test cache initialization and indexes."""
    indexes = test_cache.collection.list_indexes()
    index_names = [idx["name"] for idx in indexes]

    assert "_id_" in index_names
    assert "text_hash_1_model_1" in index_names
    assert "created_at_1" in index_names

def test_cache_set_get(test_cache):
    """Test basic set and get operations."""
    text = "test text"
    model = "test-model"
    embedding = np.array([1.0, 2.0, 3.0])

    # Test set
    assert test_cache.set(text, model, embedding)

    # Test get
    cached = test_cache.get(text, model)
    assert cached is not None
    np.testing.assert_array_equal(cached, embedding)

def test_cache_get_many(test_cache):
    """Test batch get operations."""
    texts = ["text1", "text2", "text3"]
    model = "test-model"
    embeddings = [
        np.array([1.0, 2.0]),
        np.array([3.0, 4.0]),
        np.array([5.0, 6.0])
    ]

    # Set multiple embeddings
    test_cache.set_many(texts, model, embeddings)

    # Test get_many
    results = test_cache.get_many(texts, model)
    assert len(results) == len(texts)

    for (pos, embedding), expected in zip(results, embeddings):
        assert embedding is not None
        np.testing.assert_array_equal(embedding, expected)

def test_cache_cleanup_before(test_cache):
    """Test cleanup of entries before timestamp."""
    text1 = "old text"
    text2 = "new text"
    model = "test-model"
    embedding = np.array([1.0, 2.0, 3.0])

    # Set with old timestamp
    old_time = datetime.utcnow() - timedelta(days=7)
    with patch('search.utils.llm_cache.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = old_time
        test_cache.set(text1, model, embedding)

    # Set with current timestamp
    test_cache.set(text2, model, embedding)

    # Cleanup entries older than 3 days
    cleanup_time = datetime.utcnow() - timedelta(days=3)
    stats = test_cache.cleanup_before(cleanup_time)

    # Verify cleanup
    assert stats["deleted_count"] == 1
    assert test_cache.get(text1, model) is None  # Old entry should be gone
    assert test_cache.get(text2, model) is not None  # New entry should remain

def test_cache_clear(test_cache):
    """Test clearing all cache entries."""
    text = "test text"
    model = "test-model"
    embedding = np.array([1.0, 2.0, 3.0])

    # Add entry
    test_cache.set(text, model, embedding)
    assert test_cache.get(text, model) is not None

    # Clear cache
    assert test_cache.clear()

    # Verify cache is empty
    assert test_cache.get(text, model) is None