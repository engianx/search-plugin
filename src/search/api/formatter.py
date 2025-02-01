"""Search results formatter."""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from ..utils.config import load_config
from ..utils.storage import load_metadata
from ..utils.product_utils import get_product_handle

logger = logging.getLogger(__name__)

class BaseFormatter:
    """Base formatter class."""
    def format(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format a single result."""
        raise NotImplementedError

class ProductFormatter(BaseFormatter):
    """Format product search results."""
    def __init__(self, site_dir: str):
        self.site_dir = site_dir

    def get_product_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Load extracted product data from products directory."""
        product_file = os.path.join(self.site_dir, 'products', f"{get_product_handle(url)}.json")
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load product data for {url}: {str(e)}")
            return None

    def format(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        product_data = self.get_product_data(result["url"])
        if not product_data:
            return None

        return {
            "url": result["url"],
            "title": product_data.get("name", metadata.get("title", result["title"])),
            "images": product_data.get("images", metadata.get("images", [])),
            "highlights": product_data.get("features", [result["content"]]),
            "specifications": product_data.get("specifications", {}),
            "price": product_data.get("price"),
            "description": product_data.get("description")
        }

class DocumentFormatter(BaseFormatter):
    """Format document search results."""
    def format(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": result["url"],
            "content": result["content"]
        }

class QuestionFormatter(BaseFormatter):
    """Format question/answer search results."""
    def format(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": result["url"],
            "content": result["metadata"]["answer"]  # Use answer from metadata instead of content
        }

class SearchResultFormatter:
    """Format search results into API response format."""

    def __init__(self, site_dir: str, config: Dict[str, Any]):
        """Initialize formatter."""
        self.config = config
        self.max_products = config["api"]["search"]["max_products"]
        self.product_boost = config.get("ranking", {}).get("product_boost", 1.0)
        self.site_dir = site_dir

        # Initialize formatters
        self.formatters = {
            "product": ProductFormatter(site_dir),
            "document": DocumentFormatter(),
            "answer": QuestionFormatter()
        }

        # Load sitemap metadata
        sitemap_file = os.path.join(site_dir, 'sitemap_metadata.json')
        if not os.path.exists(sitemap_file):
            raise FileNotFoundError(f"Sitemap metadata not found: {sitemap_file}")
        self.sitemap_metadata = load_metadata(sitemap_file)

    def format_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format search results into API response format."""
        # Apply product boost to scores
        for result in search_results:
            url = result["url"]
            metadata = self.sitemap_metadata.get(url)
            if metadata and metadata["page_type"] == "product":
                result["score"] *= self.product_boost

        # Sort results by boosted score
        sorted_results = sorted(search_results, key=lambda x: x["score"], reverse=True)

        if not sorted_results:
            return {"products": [], "answer": None}

        # Process first result
        first_result = sorted_results[0]
        first_url = first_result["url"]
        first_metadata = self.sitemap_metadata.get(first_url)

        if not first_metadata:
            logger.warning(f"No sitemap metadata found for URL: {first_url}")
            return {"products": [], "answer": None}

        chunk_type = first_result.get("chunk_type", first_metadata.get("page_type"))

        # If first result is a document or answer, return only that
        if chunk_type in ["document", "answer"]:
            formatter = self.formatters[chunk_type]
            return {
                "products": [],
                "answer": formatter.format(first_result, first_metadata)
            }

        # Otherwise, return only products
        products = []
        for result in sorted_results:
            if len(products) >= self.max_products:
                break

            url = result["url"]
            metadata = self.sitemap_metadata.get(url)
            if not metadata:
                logger.warning(f"No sitemap metadata found for URL: {url}")
                continue

            chunk_type = result.get("chunk_type", metadata.get("page_type"))
            if chunk_type == "product":
                formatted_product = self.formatters["product"].format(result, metadata)
                if formatted_product:
                    products.append(formatted_product)

        return {
            "products": products,
            "answer": None
        }