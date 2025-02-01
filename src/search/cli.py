"""Command line interface for the search."""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=broad-exception-caught
import os
import glob
import logging
from datetime import datetime
from urllib.parse import urlparse
import click
from dotenv import load_dotenv
from scrapy.utils.log import configure_logging
from .sitemap.crawler import run_spider as run_sitemap_spider
from .page.crawler import run_spider as run_page_spider
from .processor.document import process_site, generate_qa
from .indexer.driver import index_documents, index_question_and_answer
from .utils.config import load_config
from .processor.product import process_site as process_products

# Load environment variables from .env file
load_dotenv()

def get_openai_key():
    """Get OpenAI API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise click.UsageError(
            'OpenAI API key not found. Set OPENAI_API_KEY environment variable '
            'or add it to .env file'
        )
    return api_key

def cleanup_old_logs(logs_dir, prefix, keep_last_n=2):
    """Keep only the N most recent log files for a given prefix.

    Args:
        logs_dir: Directory containing log files
        prefix: Log file prefix (e.g., 'sitemap', 'pages')
        keep_last_n: Number of most recent logs to keep
    """
    # List all log files for this prefix
    log_files = glob.glob(os.path.join(logs_dir, f'{prefix}_*.log'))

    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # Remove all but the last N files
    for log_file in log_files[keep_last_n:]:
        try:
            os.remove(log_file)
            logging.debug(f"Removed old log file: {log_file}")
        except OSError as e:
            logging.warning(f"Failed to remove old log file {log_file}: {e}")

def setup_logging(site_dir, prefix, keep_logs=2):
    """Setup logging to both file and console."""
    # Create logs directory
    logs_dir = os.path.join(site_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create a timestamp for the log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'{prefix}_{timestamp}.log')

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Configure Scrapy logging
    configure_logging(install_root_handler=False)
    logging.getLogger('scrapy').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    # Clean up old log files for this prefix
    cleanup_old_logs(logs_dir, prefix, keep_logs)

    return log_file

def get_domain_from_url(url):
    """Extract domain from URL."""
    return urlparse(url).netloc

def get_data_dir():
    """Get default data directory from config."""
    config = load_config()
    return config.get('data_dir', '/data/search')

@click.group()
def cli():
    """Website scraper CLI with individual step commands."""
    pass

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
def sitemap(url, data_dir):
    """Crawl website sitemap and save URL metadata.

    URL: The website URL to crawl
    DATA_DIR: Directory (+domain subdir) to store the website data (default from config)

    Output files:
    - {data_dir}/{domain}/sitemap_metadata.json: Basic URL metadata (paths and types)
    - {data_dir}/{domain}/sitemap_stats.json: Sitemap crawl statistics
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)
    os.makedirs(site_dir, exist_ok=True)

    setup_logging(site_dir, 'sitemap')

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting sitemap crawler for: {url}")
        logger.info(f"Output directory: {site_dir}")
        run_sitemap_spider(url=url, site_dir=site_dir)
        logger.info("Sitemap crawling completed successfully!")
    except Exception as e:
        logger.error(f"Error during sitemap crawling: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--proxy-service', type=click.Choice(['zenrows', 'none']), default='none')
@click.option('--proxy-api-key', help='API key for the proxy service')
def pages(url, data_dir, proxy_service, proxy_api_key):
    """Crawl pages listed in sitemap metadata.

    URL: The website URL to crawl
    DATA_DIR: Directory (+domain subdir) to read sitemap_metadata.json (default from config)

    Input files:
    - {data_dir}/{domain}/sitemap_metadata.json: Basic URL metadata from sitemap

    Output files:
    - {data_dir}/{domain}/pages_metadata.json: Detailed page metadata with crawl status
    - {data_dir}/{domain}/pages_stats.json: Page crawl statistics
    - Saves HTML content to paths specified in metadata
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)
    if not os.path.exists(os.path.join(site_dir, 'sitemap_metadata.json')):
        raise click.BadParameter(
            f'sitemap_metadata.json not found in {site_dir}. Run sitemap command first.'
        )

    setup_logging(site_dir, 'pages')

    logger = logging.getLogger(__name__)

    # Setup proxy configuration
    proxy_config = None
    if proxy_service != 'none':
        if not proxy_api_key:
            raise click.BadParameter('Proxy API key is required when using a proxy service')
        proxy_config = {
            'service': proxy_service,
            'api_key': proxy_api_key
        }

    try:
        logger.info("Starting page crawler")
        run_page_spider(site_dir=site_dir, proxy_config=proxy_config)
        logger.info("Page crawling completed successfully!")
    except Exception as e:
        logger.error(f"Error during page crawling: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--workers', type=int, help='Number of worker threads')
def process(url, data_dir, workers):
    """Process crawled pages and extract text content.

    URL: The website URL to process
    DATA_DIR: Directory (+domain subdir) to read pages_metadata.json (default from config)

    Input files:
    - {data_dir}/{domain}/pages_metadata.json: Page metadata from crawler

    Output files:
    - {data_dir}/{domain}/docs_metadata.json: Document metadata with extracted content
    - Saves text content to docs/ directory with paths matching original structure
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)

    # Check for required input file
    if not os.path.exists(os.path.join(site_dir, 'pages_metadata.json')):
        raise click.BadParameter(
            f'pages_metadata.json not found in {site_dir}. Run pages command first.'
        )

    # Setup logging
    setup_logging(site_dir, 'process')
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting document processor")
        stats = process_site(site_dir=site_dir, max_workers=workers)
        logger.info("Document processing completed successfully!")
        logger.info(f"Processed {stats['total_processed']} documents")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
    except Exception as e:
        logger.error(f"Error during document processing: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--batch-size', type=int, help='Override batch size from config')
def index(url, data_dir, batch_size):
    """Index processed documents in Elasticsearch.

    URL: The website URL to index
    DATA_DIR: Directory (+domain subdir) containing processed documents (default from config)

    Input files:
    - {data_dir}/{domain}/docs_metadata.json: Document metadata from processor
    - Document content files in docs/ directory

    Output files:
    - {data_dir}/{domain}/index_stats.json: Indexing statistics
    - Creates/updates Elasticsearch index named after domain
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)

    # Check for required input file
    if not os.path.exists(os.path.join(site_dir, 'docs_metadata.json')):
        raise click.BadParameter(
            f'docs_metadata.json not found in {site_dir}. Run process command first.'
        )

    # Setup logging
    setup_logging(site_dir, 'index')
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting document indexer")
        stats = index_documents(
            site_dir=site_dir,
            batch_size=batch_size
        )
        logger.info("Document indexing completed successfully!")
        logger.info(f"Indexed {stats['successful']} documents")
        logger.info(f"Failed: {len(stats['failed'])}")
        if stats['failed']:
            logger.warning("Failed URLs:")
            for url in stats['failed']:
                logger.warning(f"  {url}")
    except Exception as e:
        logger.error(f"Error during document indexing: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--workers', type=int, help='Number of worker threads')
def products(url, data_dir, workers):
    """Process product pages and extract specifications.

    URL: The website URL to process
    DATA_DIR: Directory (+domain subdir) to read sitemap_metadata.json (default from config)

    Input files:
    - {data_dir}/{domain}/sitemap_metadata.json: Page metadata from sitemap

    Output files:
    - {data_dir}/{domain}/product_metadata.json: Product metadata with extracted specs
    - {data_dir}/{domain}/product_stats.json: Processing statistics
    - Saves product data and cleaned HTML to products/ directory
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)

    # Check for required input file
    if not os.path.exists(os.path.join(site_dir, 'sitemap_metadata.json')):
        raise click.BadParameter(
            f'sitemap_metadata.json not found in {site_dir}. Run sitemap command first.'
        )

    # Setup logging
    setup_logging(site_dir, 'products')
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting product processor")
        stats = process_products(
            site_dir=site_dir,
            domain=domain,
            max_workers=workers
        )
        logger.info("Product processing completed successfully!")
        logger.info(f"Processed {stats['total_processed']} products")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
    except Exception as e:
        logger.error(f"Error during product processing: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--workers', type=int, help='Number of worker threads')
def qa(url, data_dir, workers):
    """Generate Q&A pairs for processed documents.

    URL: The website URL to process
    DATA_DIR: Directory (+domain subdir) to read docs_metadata.json (default from config)

    Input files:
    - {data_dir}/{domain}/docs_metadata.json: Document metadata from processor
    - Document content files in docs/ directory

    Output files:
    - {data_dir}/{domain}/qa_stats.json: Q&A generation statistics
    - Saves Q&A pairs as .qa.json files next to document content files
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)

    # Check for required input file
    if not os.path.exists(os.path.join(site_dir, 'docs_metadata.json')):
        raise click.BadParameter(
            f'docs_metadata.json not found in {site_dir}. Run process command first.'
        )

    # Setup logging
    setup_logging(site_dir, 'qa')
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Q&A generation")
        stats = generate_qa(site_dir=site_dir, max_workers=workers)
        logger.info("Q&A generation completed successfully!")
        logger.info(f"Processed {stats['total_processed']} documents")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
    except Exception as e:
        logger.error(f"Error during Q&A generation: {str(e)}", exc_info=True)
        raise click.Abort()

@cli.command()
@click.argument('url')
@click.argument('data_dir', type=click.Path(), default=None, required=False)
@click.option('--batch-size', type=int, help='Override batch size from config')
def index_qa(url, data_dir, batch_size):
    """Index Q&A pairs in Elasticsearch.

    URL: The website URL to index
    DATA_DIR: Directory (+domain subdir) containing processed documents (default from config)

    Input files:
    - {data_dir}/{domain}/docs_metadata.json: Document metadata from processor
    - Q&A files (.qa.json) next to document content files

    Output files:
    - {data_dir}/{domain}/qa_index_stats.json: Indexing statistics
    - Updates Elasticsearch index named after domain
    """
    data_dir = data_dir or get_data_dir()
    domain = get_domain_from_url(url)
    site_dir = os.path.join(data_dir, domain)

    # Check for required input file
    if not os.path.exists(os.path.join(site_dir, 'docs_metadata.json')):
        raise click.BadParameter(
            f'docs_metadata.json not found in {site_dir}. Run process command first.'
        )

    # Setup logging
    setup_logging(site_dir, 'index_qa')
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Q&A indexer")
        stats = index_question_and_answer(
            site_dir=site_dir,
            batch_size=batch_size
        )
        logger.info("Q&A indexing completed successfully!")
        logger.info(f"Indexed {stats['successful']} documents")
        logger.info(f"Failed: {len(stats['failed'])}")
        if stats['failed']:
            logger.warning("Failed URLs:")
            for url in stats['failed']:
                logger.warning(f"  {url}")
    except Exception as e:
        logger.error(f"Error during Q&A indexing: {str(e)}", exc_info=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()