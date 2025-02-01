"""Question-Answer generator for web content."""
import logging
from typing import Dict, List
from ..utils.llm_chat import ChatCompletionGenerator
from ..utils.json_utils import load_json

logger = logging.getLogger(__name__)

def generate_qa_pairs(chat: ChatCompletionGenerator, content: str) -> List[Dict[str, str]]:
    """Generate question-answer pairs from content using LLM.

    Args:
        chat: ChatCompletionGenerator instance
        content: Page content text

    Returns:
        list: List of Q&A dictionaries with 'question' and 'answer' keys
    """
    system_prompt = """You are a question-answer generator. Analyze the provided content and generate meaningful,
    non-repetitive questions and their corresponding factual answers based solely on the given content. Follow these rules:

    1. Only generate Q&A pairs for meaningful, informative content
    2. Avoid redundant questions about the same information
    3. Focus on key facts, specifications, and important details
    4. Ensure answers are directly supported by the content
    5. Generate 3-8 Q&A pairs depending on content richness
    6. Use natural, conversational question phrasing

    Do not generate Q&A pairs of prices, availability, discounts, etc, anything that can dynamically change.

    Return the Q&A pairs as a JSON array of objects with 'question' and 'answer' fields."""

    try:
        result = chat.generate_with_context(
            system_prompt=system_prompt,
            user_message=content,
            temperature=0.3
        )

        # Parse the response using load_json from json_utils
        qa_pairs = load_json(result)

        # Validate format
        if not isinstance(qa_pairs, list):
            raise ValueError("LLM response is not a list")

        for qa in qa_pairs:
            if not isinstance(qa, dict) or 'question' not in qa or 'answer' not in qa:
                raise ValueError("Invalid Q&A format in LLM response")

        return qa_pairs

    except Exception as e:
        logger.error(f"Failed to generate Q&A pairs: {str(e)}")
        return []