"""Elasticsearch document indexer."""
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from elasticsearch import Elasticsearch
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.embeddings import EmbeddingsGenerator
from ..utils.config import load_config

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """Index documents with embeddings in Elasticsearch."""

    def __init__(self, domain: str, embeddings: EmbeddingsGenerator):
        """Initialize indexer.

        Args:
            domain: Domain name (used as index name)
            embeddings: Embeddings generator instance
        """
        config = load_config()
        self.es = Elasticsearch(config["elasticsearch"]["uri"])
        self.embeddings = embeddings
        self.domain = domain
        self.config = config

        # Ensure index exists with proper mapping
        self._create_index()

    def _create_index(self):
        """Create index with dense vector mapping if it doesn't exist."""
        if not self.es.indices.exists(index=self.domain):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "url": {"type": "keyword"},
                        "chunks": {
                            "type": "nested",
                            "properties": {
                                "content": {"type": "text"},
                                "position": {"type": "integer"},
                                "chunk_type": {"type": "keyword"},
                                "metadata": {"type": "object"},
                                "vector": {
                                    "type": "dense_vector",
                                    "dims": 1536,  # OpenAI embedding dimension
                                    "index": True,
                                    "similarity": "cosine"
                                }
                            }
                        }
                    }
                }
            }
            self.es.indices.create(index=self.domain, body=mapping)
            logger.info(f"Created index '{self.domain}' with vector mapping")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _index_with_chunks(self, doc_id: str, title: str, chunks: List[Dict], metadata: Dict = None) -> bool:
        """Index document with text chunks, generating vectors internally."""
        try:
            # Extract content from chunk dictionaries
            chunk_texts = [chunk['content'] for chunk in chunks]
            chunk_vectors = self.embeddings.generate(chunk_texts)

            document = {
                "title": title,
                "url": doc_id,
                "chunks": [
                    {
                        "content": chunk['content'],
                        "position": i,
                        "chunk_type": chunk['chunk_type'],
                        "metadata": chunk.get('metadata', {}),
                        "vector": vector.tolist()
                    }
                    for i, (chunk, vector) in enumerate(zip(chunks, chunk_vectors))
                ]
            }
            self.es.index(index=self.domain, id=doc_id, body=document, refresh=True)
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {str(e)}")
            raise

    def index_batch_with_chunks(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index a batch of pre-chunked documents.

        Args:
            documents: List of documents with format:
                {
                    'url': str,
                    'title': str,
                    'chunks': List[Dict] where each dict has:
                        - content: str
                        - chunk_type: str
                        - metadata: Dict (optional)
                }

        Returns:
            Dict with success count and failed URLs
        """
        results = {"success": 0, "failed": []}

        with ThreadPoolExecutor() as executor:
            future_to_doc = {
                executor.submit(
                    self._index_with_chunks,
                    doc_id=doc["url"],
                    title=doc["title"],
                    chunks=doc["chunks"]
                ): doc
                for doc in documents
            }

            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    if future.result():
                        results["success"] += 1
                except Exception as e:
                    results["failed"].append(doc["url"])
                    logger.error(f"Failed to index {doc['url']}: {str(e)}")

        return results
