"""OpenAI embeddings utility."""
import os
import logging
import numpy as np
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from .llm_cache import LLMCallCache
from ..utils.config import load_config
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EmbeddingsGenerator:
    """Generate embeddings using OpenAI's API with caching."""

    def __init__(self, model: str = "text-embedding-3-small"):
        """Initialize the embeddings generator.

        Args:
            model: Model to use for embeddings (default: text-embedding-3-small)
            cache: Optional LLMCallCache instance for embeddings

        Raises:
            ValueError: If API key is not found in environment
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                'OpenAI API key not found. Set OPENAI_API_KEY environment variable '
                'or add it to .env file, or pass it explicitly.'
            )

        config = load_config()
        mongodb_uri = config['mongodb']['uri']
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.cache = LLMCallCache[np.ndarray](mongodb_uri=mongodb_uri, collection="embeddings_cache")
        logger.info(f"Initialized embeddings generator with model: {model}")

    def generate(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process in each API call

        Returns:
            np.ndarray: Array of embeddings, shape (n_texts, embedding_dim)

        Raises:
            ValueError: If texts is empty or contains invalid items
            RuntimeError: If API call fails
        """
        if not texts:
            raise ValueError("No texts provided")

        # Initialize result array
        embeddings = [None] * len(texts)
        texts_to_embed = []
        cache_positions = []

        # Check cache first
        if self.cache:
            cache_results = self.cache.get_many(texts, self.model)
            for pos, embedding in cache_results:
                if embedding is not None:
                    embeddings[pos] = embedding
                    logger.debug(f"Cache hit for text {pos}")
                else:
                    texts_to_embed.append(texts[pos])
                    cache_positions.append(pos)
                    logger.debug(f"Cache miss for text {pos}")
        else:
            texts_to_embed = texts
            cache_positions = list(range(len(texts)))

        # Generate embeddings for cache misses
        if texts_to_embed:
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i + batch_size]
                batch_positions = cache_positions[i:i + batch_size]
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch
                    )
                    # Extract embeddings from response
                    batch_embeddings = [np.array(item.embedding) for item in response.data]
                    logger.debug(f"Generated embeddings for batch {i//batch_size + 1}")

                    # Update result array
                    for pos, embedding in zip(batch_positions, batch_embeddings):
                        embeddings[pos] = embedding

                    # Cache new embeddings
                    if self.cache:
                        self.cache.set_many(batch, self.model, batch_embeddings)

                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}: {str(e)}")
                    raise RuntimeError(f"OpenAI API error: {str(e)}")

        return np.array(embeddings)

    def generate_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            np.ndarray: Embedding vector

        Raises:
            ValueError: If text is empty
            RuntimeError: If API call fails
        """
        if not text:
            raise ValueError("Empty text provided")

        embeddings = self.generate([text])
        return embeddings[0]