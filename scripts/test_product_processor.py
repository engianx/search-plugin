#!/usr/bin/env python3
"""Test script for product processor."""
import os
import sys
import json
import logging
from urllib.parse import urlparse
from argparse import ArgumentParser
from src.search.processor.product import process_product
from src.search.utils.config import load_config
from src.search.utils.storage import load_metadata

def setup_logging():
    """Setup basic logging to console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point."""
    parser = ArgumentParser(description='Test product processor on a single HTML file')
    parser.add_argument('url', help='Product page URL')
    parser.add_argument('data_dir', help='Directory containing site data')

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load domain config
        domain = urlparse(args.url).netloc
        config = load_config(domain)
        system_prompt = config.get('product_processor', {}).get('system_prompt')
        if not system_prompt:
            logger.error(f"Product processor system prompt not found in config for domain: {domain}")
            sys.exit(1)

        site_dir = os.path.join(args.data_dir, domain)
        # Load sitemap metadata
        sitemap_metadata_file = os.path.join(site_dir, 'sitemap_metadata.json')
        if not os.path.exists(sitemap_metadata_file):
            logger.error(f"Sitemap metadata file not found: {sitemap_metadata_file}")
            sys.exit(1)

        sitemap_metadata = load_metadata(sitemap_metadata_file)

        # Get HTML file path from metadata
        if args.url not in sitemap_metadata:
            logger.error(f"URL not found in sitemap metadata: {args.url}")
            sys.exit(1)

        html_file = os.path.join(site_dir, sitemap_metadata[args.url]['local_file'])
        if not os.path.exists(html_file):
            logger.error(f"HTML file not found: {html_file}")
            sys.exit(1)
        reduced_file = f"{html_file}.reduced"
        if os.path.exists(reduced_file):
            html_file = reduced_file

        # Process the product
        logger.info(f"Processing URL: {args.url}")
        logger.info(f"HTML file: {html_file}")
        product_data = process_product(
            html_path=html_file,
            system_prompt=system_prompt,
        )

        # Print results to console
        print("\nExtracted Product Data:")
        print(json.dumps(product_data, indent=2))

    except Exception as e:
        logger.error(f"Error processing product: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()