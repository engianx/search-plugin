"""Product page processor."""
import os
import logging
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from urllib.parse import urlparse
from ..utils.storage import load_metadata, save_metadata, save_stats
from ..utils.config import load_config
from ..utils.llm_chat import ChatCompletionGenerator
from ..utils.json_utils import load_json
from ..utils.product_utils import get_product_handle

logger = logging.getLogger(__name__)

def get_product_filename(url: str) -> str:
    """Extract filename from product URL.

    Args:
        url: Product page URL
        ext: File extension (default: .json)

    Returns:
        str: Filename for product file
    """
    return f"{get_product_handle(url)}.json"

def process_product(chat: ChatCompletionGenerator, html_path: str, system_prompt: str) -> Dict[str, Any]:
    """Process a single product page using OpenAI.

    Args:
        html_path: Path to HTML file
        system_prompt: System prompt for specification extraction

    Returns:
        dict: Extracted product specifications

    Raises:
        FileNotFoundError: If HTML file doesn't exist
    """
    # Read HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract specifications using cleaned HTML
    result = chat.generate_with_context(
        system_prompt=system_prompt,
        user_message=html_content,
        temperature=0.1  # Low temperature for consistent extraction
    )

    # Parse JSON response
    try:
        specs = load_json(result)
        return specs
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
        raise

def process_site(site_dir: str, domain: str, max_workers: int = None) -> Dict[str, Any]:
    """Process all product pages in a site.

    Args:
        site_dir: Directory containing site data
        domain: Domain name for loading config
        max_workers: Maximum number of worker threads

    Returns:
        dict: Processing statistics
    """
    logger.info(f"Starting product processing for: {site_dir}")

    # Initialize paths
    sitemap_metadata_file = os.path.join(site_dir, 'sitemap_metadata.json')
    product_metadata_file = os.path.join(site_dir, 'product_metadata.json')
    product_stats_file = os.path.join(site_dir, 'product_stats.json')
    products_dir = os.path.join(site_dir, 'products')
    os.makedirs(products_dir, exist_ok=True)

    # Load sitemap metadata
    sitemap_metadata = load_metadata(sitemap_metadata_file)

    # Filter product pages
    product_pages = {
        url: meta for url, meta in sitemap_metadata.items()
        if meta.get('page_type') == 'product'
    }
    logger.info(f"Found {len(product_pages)} product pages to process")

    # Load domain config
    config = load_config(domain)
    system_prompt = config.get('product_processor', {}).get('system_prompt')
    if not system_prompt:
        raise ValueError("Product processor system prompt not found in config")

    # Initialize stats
    stats = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0
    }

    # Initialize product metadata
    product_metadata = {}

    def process_page(chat: ChatCompletionGenerator, url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single product page."""
        try:
            # Get HTML file path
            html_file = os.path.join(site_dir, metadata['local_file'])
            reduced_file = f"{html_file}.reduced"
            if os.path.exists(reduced_file):
                html_file = reduced_file

            # Process the product
            product_data = process_product(chat, html_file, system_prompt)

            # Save product data
            output_path = os.path.join(products_dir, get_product_filename(url))
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2)

            # Update stats
            stats['successful'] += 1

            # Return metadata
            return {
                'local_file': os.path.relpath(output_path, site_dir)
            }

        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")
            stats['failed'] += 1
            return None

        finally:
            stats['total_processed'] += 1

    # Process pages in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        chat = ChatCompletionGenerator()

        future_to_url = {
            executor.submit(process_page, chat, url, meta): url
            for url, meta in product_pages.items()
        }

        for future in tqdm(as_completed(future_to_url), total=len(future_to_url), desc="Processing pages"):
            url = future_to_url[future]
            try:
                product_meta = future.result()
                if product_meta:
                    product_metadata[url] = product_meta
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                stats['failed'] += 1

    # Save metadata and stats
    save_metadata(product_metadata, product_metadata_file)
    save_stats(stats, product_stats_file)

    logger.info("Processing completed:")
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")

    return stats