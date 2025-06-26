"""OpenAI client configuration and utilities."""

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import List, Optional
import time
from config.settings import settings
from utils.logger import logger


class OpenAIClient:
    """Configured OpenAI client with error handling and retry logic."""

    def __init__(self):
        """Initialize the OpenAI client with configuration."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.CHAT_MODEL
        self.max_retries = settings.MAX_RETRIES

        logger.info(f"OpenAI client initialized with model: {self.model}")

    def create_chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Optional[str]:
        """
        Create a chat completion with retry logic.

        Args:
            messages: List of messages for the completion
            model: Model to use (defaults to configured model)
            max_retries: Maximum number of retries (defaults to configured max_retries)

        Returns:
            The completion content or None if all retries failed
        """
        model = model or self.model
        max_retries = max_retries or self.max_retries

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Attempting OpenAI completion (attempt {attempt + 1}/{max_retries})"
                )

                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=settings.CHAT_TEMPERATURE,
                    top_p=settings.CHAT_TOP_P,
                    frequency_penalty=settings.CHAT_FREQUENCY_PENALTY,
                    presence_penalty=settings.CHAT_PRESENCE_PENALTY,
                    max_tokens=settings.CHAT_MAX_TOKENS,
                )

                content = response.choices[0].message.content
                logger.debug(f"OpenAI completion successful on attempt {attempt + 1}")
                return content

            except Exception as e:
                logger.warning(
                    f"OpenAI completion attempt {attempt + 1} failed: {str(e)}"
                )

                if attempt == max_retries - 1:
                    logger.error(
                        f"All OpenAI completion attempts failed after {max_retries} tries"
                    )
                    return None

                # Exponential backoff
                wait_time = 2**attempt
                logger.debug(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        return None

    def test_connection(self) -> bool:
        """
        Test the OpenAI connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing OpenAI connection...")

            test_messages: List[ChatCompletionMessageParam] = [
                {"role": "user", "content": "Hello"}
            ]

            response = self.client.chat.completions.create(
                model=self.model, messages=test_messages, max_tokens=1
            )

            logger.info("OpenAI connection test successful")
            return True

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False


# Global OpenAI client instance
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """
    Get the global OpenAI client instance (singleton pattern).

    Returns:
        The configured OpenAI client
    """
    global _openai_client

    if _openai_client is None:
        _openai_client = OpenAIClient()

    return _openai_client


def create_chat_completion(
    messages: List[ChatCompletionMessageParam],
    model: Optional[str] = None,
    max_retries: Optional[int] = None,
) -> Optional[str]:
    """
    Convenience function for creating chat completions.

    Args:
        messages: List of messages for the completion
        model: Model to use (defaults to configured model)
        max_retries: Maximum number of retries (defaults to configured max_retries)

    Returns:
        The completion content or None if failed
    """
    client = get_openai_client()
    return client.create_chat_completion(messages, model, max_retries)
