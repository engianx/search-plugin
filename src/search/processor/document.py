"""Document processor implementation."""
import os
import logging
import json
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from .html import process_html
from .pdf import process_pdf
from ..utils.storage import load_metadata, save_metadata, save_stats
from ..utils.llm_chat import ChatCompletionGenerator
from ..utils.config import load_config
from .qa import generate_qa_pairs

logger = logging.getLogger(__name__)

def process_document(file_path: str, chat: ChatCompletionGenerator = None) -> Dict[str, Any]:
    """Process a document file and extract structured data.

    Args:
        file_path: Path to the document file (HTML or PDF)
        chat: Optional ChatCompletionGenerator for content rewriting

    Returns:
        dict: Extracted data with standard fields:
            - title: str, document title
            - content: str, main text content (rewritten if chat provided)

    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Select appropriate processor
    if ext == '.pdf':
        return process_pdf(file_path)
    else:
        return process_html(file_path, chat)  # Pass chat to HTML processor

def process_site(site_dir: str, max_workers: int = None) -> Dict[str, Any]:
    """Process all documents in a site directory.

    Args:
        site_dir: Directory containing site data
        max_workers: Maximum number of worker threads

    Returns:
        dict: Processing statistics
    """
    logger.info(f"Starting document processing for: {site_dir}")

    # Initialize paths
    pages_metadata_file = os.path.join(site_dir, 'pages_metadata.json')
    docs_metadata_file = os.path.join(site_dir, 'docs_metadata.json')
    docs_stats_file = os.path.join(site_dir, 'docs_stats.json')
    docs_dir = os.path.join(site_dir, 'docs')

    # Initialize stats
    stats = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'total_bytes': 0
    }

    # Load pages metadata
    pages_metadata = load_metadata(pages_metadata_file)
    logger.info(f"Found {len(pages_metadata)} pages to process")

    # Initialize docs metadata
    docs_metadata = {}

    def process_page(chat: ChatCompletionGenerator, url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single page."""
        try:
            # Skip failed pages
            if metadata.get('crawl_status') != 'success':
                logger.warning(f"Skipping failed page: {url}")
                return None

            # Process the document
            input_file = os.path.join(site_dir, metadata['local_file'])
            doc_data = process_document(input_file, chat)

            # Create output path
            rel_path = os.path.relpath(metadata['local_file'], 'html')
            base_path = os.path.splitext(rel_path)[0]
            output_path = os.path.join(docs_dir, f"{base_path}.txt")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save processed content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc_data['content'])
                logger.info(f"Processed content saved to: {output_path}")

            if 'reduced' in doc_data:
                reduced_path = f"{input_file}.reduced"
                with open(reduced_path, 'w', encoding='utf-8') as f:
                    f.write(doc_data['reduced'])

            # Update stats
            stats['successful'] += 1
            stats['total_bytes'] += len(doc_data['content'])

            # Return document metadata
            return {
                'title': doc_data['title'],
                'local_file': os.path.relpath(output_path, site_dir),
                'page_type': metadata.get('page_type', 'doc')  # Copy page_type from pages_metadata
            }

        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")
            stats['failed'] += 1
            return None

        finally:
            stats['total_processed'] += 1

    # Process pages in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a ChatCompletionGenerator instance
        chat = ChatCompletionGenerator()

        # Submit all pages for processing
        future_to_url = {
            executor.submit(process_page, chat, url, meta): url
            for url, meta in pages_metadata.items()
        }

        # Collect results as they complete
        for future in tqdm(as_completed(future_to_url), total=len(future_to_url), desc="Processing pages"):
            url = future_to_url[future]
            try:
                doc_meta = future.result()
                if doc_meta:
                    docs_metadata[url] = doc_meta
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                stats['failed'] += 1

    # Save docs metadata and stats
    save_metadata(docs_metadata, docs_metadata_file)
    save_stats(stats, docs_stats_file)
    logger.info("Processing completed:")
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")

    return stats

def generate_qa(site_dir: str, max_workers: int = None) -> Dict[str, Any]:
    """Generate Q&A pairs for all processed documents in a site directory.

    Args:
        site_dir: Directory containing site data
        max_workers: Maximum number of worker threads

    Returns:
        dict: Generation statistics
    """
    logger.info(f"Starting Q&A generation for: {site_dir}")

    # Initialize paths
    docs_metadata_file = os.path.join(site_dir, 'docs_metadata.json')
    qa_stats_file = os.path.join(site_dir, 'qa_stats.json')

    # Initialize stats
    stats = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'filtered': 0
    }

    # Load docs metadata
    docs_metadata = load_metadata(docs_metadata_file)
    logger.info(f"Found {len(docs_metadata)} documents to process")

    # Load domain config and get URL filters
    domain = os.path.basename(site_dir)
    config = load_config(domain)
    url_patterns = config.get('document_processor', {}).get('qa_url_patterns', [])

    logger.info(f"URL patterns: {url_patterns}")

    if url_patterns:
        url_regexes = [re.compile(pattern) for pattern in url_patterns]
    else:
        logger.info("No URL filters specified, processing all documents")
        url_regexes = []

    def should_process_url(url: str) -> bool:
        """Check if URL should be processed based on filters."""
        if not url_regexes:
            return True
        return any(regex.search(url) for regex in url_regexes)

    def process_doc(chat: ChatCompletionGenerator, url: str, metadata: Dict[str, Any]) -> bool:
        """Process a single document."""
        try:
            # Check URL filter
            if not should_process_url(url):
                logger.debug(f"Skipping URL (filtered): {url}")
                stats['filtered'] += 1
                return False

            # Read document content
            input_file = os.path.join(site_dir, metadata['local_file'])
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate Q&A pairs
            qa_pairs = generate_qa_pairs(chat, content)
            if qa_pairs:
                qa_path = f"{input_file}.qa.json"
                with open(qa_path, 'w', encoding='utf-8') as f:
                    json.dump(qa_pairs, f, indent=2)
                    logger.info(f"Q&A pairs saved to: {qa_path}")
                stats['successful'] += 1
                return True

            logger.warning(f"No Q&A pairs generated for: {url}")
            stats['failed'] += 1
            return False

        except Exception as e:
            logger.error(f"Failed to generate Q&A for {url}: {str(e)}")
            stats['failed'] += 1
            return False

        finally:
            stats['total_processed'] += 1

    # Process documents in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a ChatCompletionGenerator instance
        chat = ChatCompletionGenerator()

        # Submit all documents for processing
        future_to_url = {
            executor.submit(process_doc, chat, url, meta): url
            for url, meta in docs_metadata.items()
        }

        # Process results as they complete
        for future in tqdm(as_completed(future_to_url), total=len(future_to_url), desc="Generating Q&A"):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                stats['failed'] += 1

    # Save stats
    save_stats(stats, qa_stats_file)
    logger.info("Q&A generation completed:")
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Filtered: {stats['filtered']}")

    return stats