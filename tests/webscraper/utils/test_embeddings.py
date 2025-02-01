"""Tests for embeddings generator."""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from pymongo import MongoClient
from search.utils.embeddings import EmbeddingsGenerator
from search.utils.llm_cache import LLMCallCache
from search.utils.config import load_config

# Test configuration
TEST_DB = "test_search"
TEST_COLLECTION = "test_embeddings_cache"
MONGO_URI = load_config()["mongodb"].get("test_uri", "mongodb://localhost:27017")

# Mock OpenAI response
class MockEmbeddingResponse:
    def __init__(self, embeddings):
        self.data = [Mock(embedding=emb) for emb in embeddings]

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('search.utils.embeddings.OpenAI') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_cache():
    """Mock LLMCallCache."""
    with patch('search.utils.embeddings.LLMCallCache') as mock:
        # Create a mock that can handle the generic type
        cache = Mock()
        mock.__getitem__.return_value = mock  # Handle the generic type
        mock.return_value = cache
        yield cache

def test_generate_single(mock_openai, mock_cache):
    """Test generating single embedding."""
    # Setup mock response
    embedding = [1.0, 2.0, 3.0]
    mock_openai.embeddings.create.return_value = MockEmbeddingResponse([embedding])

    # Setup cache mock
    mock_cache.get_many.return_value = [(0, None)]  # Cache miss

    generator = EmbeddingsGenerator()

    result = generator.generate_single("test text")

    np.testing.assert_array_equal(result, np.array(embedding))
    mock_openai.embeddings.create.assert_called_once()
    assert mock_openai.embeddings.create.call_args[1]["model"] == "text-embedding-3-small"

def test_generate_batch(mock_openai, mock_cache):
    """Test generating batch embeddings."""
    # Setup mock response
    embeddings = [
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0]
    ]
    mock_openai.embeddings.create.return_value = MockEmbeddingResponse(embeddings)

    # Setup cache mock
    mock_cache.get_many.return_value = [(i, None) for i in range(3)]  # All cache misses

    texts = ["text1", "text2", "text3"]
    generator = EmbeddingsGenerator()
    results = generator.generate(texts)

    assert results.shape == (3, 2)
    np.testing.assert_array_equal(results, np.array(embeddings))

def test_generate_with_cache(mock_openai, mock_cache):
    """Test generating embeddings with cache."""
    # Setup mock response
    embeddings = [
        [1.0, 2.0],
        [3.0, 4.0]
    ]
    mock_openai.embeddings.create.return_value = MockEmbeddingResponse(embeddings)

    texts = ["text1", "text2"]

    # First call - simulate cache misses
    mock_cache.get_many.return_value = [(0, None), (1, None)]
    mock_cache.set_many = Mock()  # Add this to mock the cache setting

    generator = EmbeddingsGenerator()

    results1 = generator.generate(texts)

    # Verify first call made API request
    mock_openai.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=texts
    )

    # Second call - simulate cache hits
    mock_cache.get_many.return_value = [(0, embeddings[0]), (1, embeddings[1])]
    results2 = generator.generate(texts)

    # Verify results match
    np.testing.assert_array_equal(results1, results2)
    # Verify API was not called again
    mock_openai.embeddings.create.assert_called_once()

def test_custom_model(mock_openai, mock_cache):
    """Test using custom model."""
    custom_model = "text-embedding-ada-002"
    embedding = [1.0, 2.0, 3.0]
    mock_openai.embeddings.create.return_value = MockEmbeddingResponse([embedding])
    mock_cache.get_many.return_value = [(0, None)]

    generator = EmbeddingsGenerator(model=custom_model)
    generator.generate_single("test text")

    assert mock_openai.embeddings.create.call_args[1]["model"] == custom_model

def test_error_handling(mock_openai, mock_cache):
    """Test error handling."""
    mock_openai.embeddings.create.side_effect = Exception("API Error")
    mock_cache.get_many.return_value = [(0, None)]

    generator = EmbeddingsGenerator()

    with pytest.raises(RuntimeError):
        generator.generate(["test text"])