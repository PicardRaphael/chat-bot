"""Gemini client configuration and utilities using OpenAI API."""

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import List, Optional
import time
from config.settings import settings
from utils.logger import logger
from core.models import Evaluation


class GeminiClient:
    """Configured Gemini client using OpenAI API with custom base_url."""

    def __init__(self):
        """Initialize the Gemini client with configuration."""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        self.client = OpenAI(
            api_key=settings.GOOGLE_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )
        self.model = settings.EVALUATION_MODEL
        self.max_retries = settings.MAX_RETRIES

        logger.info(f"Gemini client initialized with model: {self.model}")

    def create_evaluation_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: Optional[int] = None,
    ) -> Optional[Evaluation]:
        """
        Create an evaluation completion with structured output.

        Args:
            system_prompt: System instructions for the evaluation
            user_prompt: User message to evaluate
            max_retries: Maximum number of retries (defaults to configured max_retries)

        Returns:
            Evaluation object or None if failed
        """
        max_retries = max_retries or self.max_retries

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Attempting Gemini evaluation completion (attempt {attempt + 1}/{max_retries})"
                )

                response = self.client.beta.chat.completions.parse(
                    model=self.model, messages=messages, response_format=Evaluation
                )

                if response.choices[0].message.parsed:
                    logger.debug(
                        f"Gemini evaluation successful on attempt {attempt + 1}"
                    )
                    return response.choices[0].message.parsed
                else:
                    logger.warning(
                        f"Gemini evaluation returned empty response on attempt {attempt + 1}"
                    )

            except Exception as e:
                logger.warning(
                    f"Gemini evaluation attempt {attempt + 1} failed: {str(e)}"
                )

                if attempt == max_retries - 1:
                    logger.error(
                        f"All Gemini evaluation attempts failed after {max_retries} tries"
                    )
                    return None

                # Exponential backoff
                wait_time = 2**attempt
                logger.debug(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        return None

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
                    f"Attempting Gemini chat completion (attempt {attempt + 1}/{max_retries})"
                )

                response = self.client.chat.completions.create(
                    model=model, messages=messages
                )

                content = response.choices[0].message.content
                if content:
                    logger.debug(
                        f"Gemini chat completion successful on attempt {attempt + 1}"
                    )
                    return content

            except Exception as e:
                logger.warning(
                    f"Gemini chat completion attempt {attempt + 1} failed: {str(e)}"
                )

                if attempt == max_retries - 1:
                    logger.error(
                        f"All Gemini chat completion attempts failed after {max_retries} tries"
                    )
                    return None

                # Exponential backoff
                wait_time = 2**attempt
                logger.debug(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        return None

    def test_connection(self) -> bool:
        """
        Test the Gemini connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing Gemini connection...")

            test_messages: List[ChatCompletionMessageParam] = [
                {"role": "user", "content": "Hello"}
            ]

            response = self.client.chat.completions.create(
                model=self.model, messages=test_messages, max_tokens=1
            )

            if response.choices[0].message.content:
                logger.info("Gemini connection test successful")
                return True
            else:
                logger.error("Gemini connection test failed: empty response")
                return False

        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return False


# Global Gemini client instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get the global Gemini client instance (singleton pattern).

    Returns:
        The configured Gemini client
    """
    global _gemini_client

    if _gemini_client is None:
        _gemini_client = GeminiClient()

    return _gemini_client


def create_evaluation_completion(
    system_prompt: str,
    user_prompt: str,
    max_retries: Optional[int] = None,
) -> Optional[Evaluation]:
    """
    Convenience function for creating evaluation completions.

    Args:
        system_prompt: System instructions for the evaluation
        user_prompt: User message to evaluate
        max_retries: Maximum number of retries (defaults to configured max_retries)

    Returns:
        Evaluation object or None if failed
    """
    client = get_gemini_client()
    return client.create_evaluation_completion(system_prompt, user_prompt, max_retries)


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
    client = get_gemini_client()
    return client.create_chat_completion(messages, model, max_retries)
