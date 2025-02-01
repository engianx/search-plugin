"""HTML document processor."""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import re
from ..utils.llm_chat import ChatCompletionGenerator

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean extracted text content.

    Args:
        text: Raw text content

    Returns:
        str: Cleaned text with normalized whitespace
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def rewrite_content(chat: ChatCompletionGenerator, content: str) -> str:
    """Rewrite content into human-readable text using LLM.

    Args:
        chat: ChatCompletionGenerator instance
        content: Raw content extracted from HTML

    Returns:
        str: Human-readable text
    """
    system_prompt = """You are a content editor. Your task is to rewrite the given text into clear,
    human-readable content while preserving all important information. Focus on:
    1. Maintaining factual accuracy
    2. Improving readability and flow
    3. Using natural language
    4. Keeping the original meaning
    5. Removing redundant or marketing language

    Return only the rewritten text, without any explanations or metadata."""

    try:
        result = chat.generate_with_context(
            system_prompt=system_prompt,
            user_message=content,
            temperature=0.3  # Lower temperature for more consistent output
        )
        return clean_text(result)
    except Exception as e:
        logger.error(f"Failed to rewrite content: {str(e)}")
        return content  # Return original content if rewriting fails

def process_html(file_path: str, chat: ChatCompletionGenerator = None) -> Dict[str, Any]:
    """Process HTML file and extract structured data.

    Args:
        file_path: Path to HTML file
        chat: Optional ChatCompletionGenerator for content rewriting

    Returns:
        dict: Extracted data with fields:
            - title: str, page title
            - content: str, main text content (rewritten if chat provided)
            - reduced: str, reduced HTML content

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If HTML parsing fails
    """
    try:
        # Read and parse HTML
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Extract title
        title = ''
        title_tag = soup.find('title')
        if title_tag:
            title = clean_text(title_tag.get_text())

        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # Extract main content
        reduced_html = ''
        main_content = soup.find('main') or soup.find('article') or soup.find('div', {'id': 'content'})
        if main_content:
            reduced_html = str(main_content)
        else:
            # Fallback: get text from body
            body = soup.find('body')
            if body:
                reduced_html = str(body)
            else:
                logger.warning(f"No main content or body found in {file_path}, using all text")
                reduced_html = str(soup)

        # Extract and clean text content
        content = clean_text(BeautifulSoup(reduced_html, 'html.parser').get_text())

        # Rewrite content if chat is provided
        if content:
            content = rewrite_content(chat, content)

        return {
            'title': title,
            'content': content,
            'reduced': reduced_html
        }

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to process HTML file {file_path}: {str(e)}")
        raise ValueError(f"HTML processing failed: {str(e)}")