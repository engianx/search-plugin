"""MongoDB-based cache for LLM calls."""
import logging
import hashlib
import pickle
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, TypeVar, Generic
import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo.operations import UpdateOne

from search.utils.config import load_config

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for cached values

project_config = load_config()

class LLMCallCache(Generic[T]):
    """Generic cache for LLM calls using MongoDB."""

    def __init__(self, mongodb_uri: str, collection: str, database: str = project_config['mongodb']['database']):
        """Initialize the cache.

        Args:
            collection: Collection name for specific cache type
            database: Database name

        Raises:
            PyMongoError: If MongoDB connection fails
        """
        self.cache_disabled = os.environ.get('DISABLE_LLM_CACHE', '').lower() in ('true', '1', 'yes')
        if self.cache_disabled:
            logger.info("LLM cache is disabled via DISABLE_LLM_CACHE environment variable")
            return

        try:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database]
            self.collection: Collection = self.db[collection]

            # Create search
            self.collection.create_index([("text_hash", 1), ("model", 1)], unique=True)
            self.collection.create_index("created_at")

            logger.info(f"Initialized LLM cache: {database}.{collection}")

        except PyMongoError as e:
            logger.error(f"Failed to initialize MongoDB cache: {str(e)}")
            raise

    def _compute_hashes(self, texts: List[str], model: str) -> List[str]:
        """Compute hashes for multiple texts.

        Args:
            texts: List of input texts
            model: Model name

        Returns:
            List[str]: List of SHA-256 hashes
        """
        return [hashlib.sha256(f"{text}:{model}".encode()).hexdigest()
                for text in texts]

    def get_many(self, texts: List[str], model: str) -> List[Tuple[int, Optional[T]]]:
        """Get cached values for multiple texts.

        Args:
            texts: List of input texts
            model: Model name

        Returns:
            List[Tuple[int, Optional[T]]]: List of (position, value) tuples
                where value is None for cache misses
        """
        if self.cache_disabled:
            return [(i, None) for i in range(len(texts))]

        try:
            text_hashes = self._compute_hashes(texts, model)

            # Fetch all matching documents
            docs = self.collection.find({
                "text_hash": {"$in": text_hashes},
                "model": model
            })

            # Create hash to document mapping
            hash_to_doc = {doc["text_hash"]: doc for doc in docs}

            # Create result list with original positions
            results = []
            for i, (text, text_hash) in enumerate(zip(texts, text_hashes)):
                doc = hash_to_doc.get(text_hash)
                if doc:
                    # Cache hit
                    value = pickle.loads(doc["value"])
                    results.append((i, value))
                else:
                    # Cache miss
                    results.append((i, None))

            return results

        except PyMongoError as e:
            logger.error(f"Cache get_many error: {str(e)}")
            return [(i, None) for i in range(len(texts))]

    def set_many(self, texts: List[str], model: str,
                values: List[T]) -> bool:
        """Store multiple values in cache.

        Args:
            texts: List of input texts
            model: Model name
            values: List of values to cache

        Returns:
            bool: True if all operations successful
        """
        if self.cache_disabled:
            return True

        try:
            text_hashes = self._compute_hashes(texts, model)
            current_time = datetime.utcnow()

            # Prepare bulk upsert operations
            operations = []
            for text, text_hash, value in zip(texts, text_hashes, values):
                doc = {
                    "text_hash": text_hash,
                    "model": model,
                    "text": text,
                    "value": pickle.dumps(value),
                    "created_at": current_time
                }
                operations.append(UpdateOne(
                    {"text_hash": text_hash, "model": model},
                    {"$set": doc},
                    upsert=True
                ))

            # Execute bulk write
            if operations:
                self.collection.bulk_write(operations)
            return True

        except PyMongoError as e:
            logger.error(f"Cache set_many error: {str(e)}")
            return False

    # Keep single-item methods for convenience
    def get(self, text: str, model: str) -> Optional[T]:
        """Get single value from cache."""
        results = self.get_many([text], model)
        return results[0][1] if results else None

    def set(self, text: str, model: str, value: T) -> bool:
        """Store single value in cache."""
        return self.set_many([text], model, [value])

    def cleanup_before(self, timestamp: datetime) -> Dict[str, Any]:
        """Remove entries created before specified timestamp.

        Args:
            timestamp: Remove entries created before this time

        Returns:
            dict: Cleanup statistics
        """
        if self.cache_disabled:
            return {"status": "cache_disabled"}

        try:
            result = self.collection.delete_many({
                "created_at": {"$lt": timestamp}
            })

            stats = {
                "deleted_count": result.deleted_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"Cache cleanup: removed {result.deleted_count} entries")
            return stats

        except PyMongoError as e:
            logger.error(f"Cache cleanup error: {str(e)}")
            return {"error": str(e)}

    def clear(self) -> bool:
        """Clear all cache entries.

        Returns:
            bool: True if successful
        """
        if self.cache_disabled:
            return True

        try:
            self.collection.delete_many({})
            logger.info("Cache cleared")
            return True

        except PyMongoError as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False