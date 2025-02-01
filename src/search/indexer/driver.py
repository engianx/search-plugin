"""Driver for document indexing."""
import os
import json
import logging
import tiktoken
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from ..utils.config import load_config
from ..utils.storage import load_metadata, save_stats
from ..utils.embeddings import EmbeddingsGenerator
from .es_indexer import DocumentIndexer
from ..utils.text_chunker import TextChunker

logger = logging.getLogger(__name__)

def _prepare_content_documents(site_dir: str, sitemap_metadata: Dict[str, Any], docs_metadata: Dict[str, Any], chunker: TextChunker) -> List[Dict[str, Any]]:
    """Prepare regular content documents for indexing."""
    documents = []
    for url, metadata in docs_metadata.items():
        content_path = os.path.join(site_dir, metadata['local_file'])
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chunks = chunker.chunk_text(content)

            # Use page_type from metadata as chunk_type, default to 'doc' if not present
            chunk_type = metadata.get('page_type', sitemap_metadata.get(url, {}).get('page_type', 'document'))

            doc = {
                'url': url,
                'title': metadata.get('title', ''),
                'chunks': [{
                    'content': chunk,
                    'chunk_type': chunk_type,
                    'metadata': None
                } for chunk in chunks]
            }
            documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to read content file {content_path}: {str(e)}")
            continue
    return documents

def _prepare_qa_documents(site_dir: str, sitemap_metadata: Dict[str, Any], docs_metadata: Dict[str, Any], chunker: TextChunker) -> List[Dict[str, Any]]:
    """Prepare QA documents for indexing."""
    documents = []
    for url, metadata in docs_metadata.items():
        content_path = os.path.join(site_dir, metadata['local_file'])
        qa_path = f"{content_path}.qa.json"

        if not os.path.exists(qa_path):
            continue

        try:
            with open(qa_path, 'r', encoding='utf-8') as f:
                qa_pairs = json.load(f)

            doc = {
                'url': url,
                'title': metadata.get('title', ''),
                'chunks': [{
                    'content': qa['question'],
                    'chunk_type': 'answer',
                    'metadata': {'answer': qa['answer']}
                } for qa in qa_pairs]
            }
            if doc['chunks']:  # Only add document if it has chunks
                documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to process QA file {qa_path}: {str(e)}")
            continue
    return documents

def _run_indexing(
    site_dir: str,
    prepare_documents: Callable[[str, Dict[str, Any], TextChunker], List[Dict[str, Any]]],
    metadata_file: str,
    stats_file: str,
    batch_size: Optional[int] = None
) -> Dict[str, Any]:
    """Common indexing logic for different document types."""
    logger.info(f"Starting document indexing for: {site_dir}")

    domain = os.path.basename(os.path.normpath(site_dir))

    # Load configuration
    config = load_config(domain)
    if not batch_size:
        batch_size = config["indexer"]["batch_size"]

    # Load document metadata
    metadata_path = os.path.join(site_dir, metadata_file)
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Document metadata not found: {metadata_path}")

    docs_metadata = load_metadata(metadata_path)

    # load sitemap metadata
    sitemap_metadata_path = os.path.join(site_dir, 'sitemap_metadata.json')
    if not os.path.exists(sitemap_metadata_path):
        raise FileNotFoundError(f"Sitemap metadata not found: {sitemap_metadata_path}")
    sitemap_metadata = load_metadata(sitemap_metadata_path)

    # Initialize statistics
    stats = {
        'total_documents': len(docs_metadata),
        'successful': 0,
        'failed': [],
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'duration_seconds': None
    }

    try:
        # Initialize embeddings generator and indexer
        embeddings = EmbeddingsGenerator()
        indexer = DocumentIndexer(domain=domain, embeddings=embeddings)
        chunker = TextChunker(
            sentence_splitters=config["indexer"]["sentence_splitters"],
            max_tokens=config["elasticsearch"]["chunk_size"]
        )

        # Prepare all documents
        documents = prepare_documents(site_dir, sitemap_metadata, docs_metadata, chunker)

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            results = indexer.index_batch_with_chunks(batch)
            stats['successful'] += results['success']
            stats['failed'].extend(results['failed'])

    except Exception as e:
        logger.error(f"Indexing error: {str(e)}", exc_info=True)
        raise

    finally:
        # Update final statistics
        stats['end_time'] = datetime.now().isoformat()
        stats['duration_seconds'] = (
            datetime.fromisoformat(stats['end_time']) -
            datetime.fromisoformat(stats['start_time'])
        ).total_seconds()

        # Save statistics
        stats_path = os.path.join(site_dir, stats_file)
        save_stats(stats, stats_path)

        logger.info(f"Indexing completed. Success: {stats['successful']}, Failed: {len(stats['failed'])}")

    return stats

def index_documents(site_dir: str, batch_size: Optional[int] = None) -> Dict[str, Any]:
    """Index processed documents in Elasticsearch.

    Args:
        site_dir: Directory containing processed documents
        batch_size: Optional override for batch size from config

    Returns:
        Dict containing indexing statistics
    """
    logger.info(f"Starting document content indexing for: {site_dir}")
    return _run_indexing(
        site_dir=site_dir,
        prepare_documents=_prepare_content_documents,
        metadata_file='docs_metadata.json',
        stats_file='index_stats.json',
        batch_size=batch_size
    )

def index_question_and_answer(site_dir: str, batch_size: Optional[int] = None) -> Dict[str, Any]:
    """Index Q&A pairs in Elasticsearch.

    Args:
        site_dir: Directory containing processed documents
        batch_size: Optional override for batch size from config

    Returns:
        Dict containing indexing statistics
    """
    logger.info(f"Starting Q&A indexing for: {site_dir}")
    return _run_indexing(
        site_dir=site_dir,
        prepare_documents=_prepare_qa_documents,
        metadata_file='docs_metadata.json',
        stats_file='qa_index_stats.json',
        batch_size=batch_size
    )