"""OpenAI chat completion utility."""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from .llm_cache import LLMCallCache
from ..utils.config import load_config
logger = logging.getLogger(__name__)

class ChatCompletionGenerator:
    """Generate chat completions using OpenAI's API."""

    def __init__(self, model: str = "gpt-4o-mini", max_retries: int = 3):
        """Initialize the chat completion generator.

        Args:
            model: Model to use for chat completion
            max_retries: Maximum number of retries for API calls
            cache_uri: MongoDB URI for caching (optional)

        Raises:
            ValueError: If API key is not found in environment
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                'OpenAI API key not found. Set OPENAI_API_KEY environment variable '
                'or add it to .env file.'
            )

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.max_retries = max_retries

        # Initialize cache if URI provided
        config = load_config()
        mongodb_uri = config['mongodb']['uri']
        self.cache = LLMCallCache[str](mongodb_uri=mongodb_uri, collection="chat_cache")
        logger.info(f"Initialized chat completion generator with model: {model}")

    def _get_cache_text(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Create cache key text from messages and parameters.

        Args:
            messages: List of message dictionaries
            temperature: Temperature parameter

        Returns:
            str: Cache key text
        """
        return f"{temperature}|" + "|".join(
            f"{msg['role']}:{msg['content']}" for msg in messages
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def generate(self, messages: List[Dict[str, str]],
                temperature: float = 0.7,
                max_tokens: Optional[int] = None) -> str:
        """Generate chat completion response with retries and caching.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (optional)

        Returns:
            str: Generated response text

        Raises:
            RuntimeError: If API call fails after retries
        """
        try:
            # Check cache first if available
            if self.cache:
                cache_text = self._get_cache_text(messages, temperature)
                cached_response = self.cache.get(cache_text, self.model)
                if cached_response is not None:
                    logger.debug("Cache hit for chat completion")
                    return cached_response

            # Generate response from API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            result = response.choices[0].message.content

            # Cache the response if cache is available
            if self.cache:
                cache_text = self._get_cache_text(messages, temperature)
                self.cache.set(cache_text, self.model, result)
                logger.debug("Cached chat completion response")

            return result

        except Exception as e:
            logger.error(f"Failed to generate chat completion: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_async(self, messages: List[Dict[str, str]],
                           temperature: float = 0.7,
                           max_tokens: Optional[int] = None) -> str:
        """Generate chat completion response asynchronously with retries.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (optional)

        Returns:
            str: Generated response text

        Raises:
            RuntimeError: If API call fails after retries
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to generate async chat completion: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_stream(self, messages: List[Dict[str, str]],
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion response with retries.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (optional)

        Yields:
            str: Generated response text chunks

        Raises:
            RuntimeError: If API call fails after retries
        """
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Failed to generate streaming chat completion: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    # Helper methods with system/user message formatting
    def generate_with_context(self, system_prompt: str, user_message: str,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None) -> str:
        """Generate chat completion with system and user messages."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.generate(messages, temperature, max_tokens)

    async def generate_with_context_async(self, system_prompt: str, user_message: str,
                                        temperature: float = 0.7,
                                        max_tokens: Optional[int] = None) -> str:
        """Generate async chat completion with system and user messages."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return await self.generate_async(messages, temperature, max_tokens)

    async def generate_with_context_stream(self, system_prompt: str, user_message: str,
                                         temperature: float = 0.7,
                                         max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion with system and user messages."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        async for chunk in self.generate_stream(messages, temperature, max_tokens):
            yield chunk