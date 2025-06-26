"""Retry service for intelligent response regeneration."""

import time
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
from config.prompts import prompt_templates
from utils.logger import logger
from core.models import Evaluation, ChatRequest, ChatResponse
from core.message_formatter import (
    build_retry_messages,
    gradio_history_to_openai_messages,
)
from core.profile_loader import get_info
from api.openai_client import create_chat_completion
from services.evaluation_service import get_evaluation_service


class RetryStrategy(Enum):
    """Retry strategy options."""

    SINGLE = "single"  # Single retry attempt
    MULTIPLE = "multiple"  # Multiple retry attempts with same feedback
    PROGRESSIVE = "progressive"  # Progressive improvement with evaluation feedback
    BEST_OF_N = "best_of_n"  # Generate multiple responses and pick the best


class RetryResult:
    """Result of a retry operation."""

    def __init__(
        self,
        final_response: str,
        was_successful: bool,
        attempts_made: int,
        final_evaluation: Optional[Evaluation] = None,
        all_attempts: Optional[List[str]] = None,
        execution_time: float = 0.0,
    ):
        self.final_response = final_response
        self.was_successful = was_successful
        self.attempts_made = attempts_made
        self.final_evaluation = final_evaluation
        self.all_attempts = all_attempts or []
        self.execution_time = execution_time


class RetryService:
    """Service for intelligent response retry with various strategies."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize the retry service.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Exponential backoff factor
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        logger.debug(f"RetryService initialized with max_retries={max_retries}")

    def get_system_prompt(self) -> str:
        """
        Generate the system prompt based on user profile.

        Returns:
            System prompt string
        """
        try:
            name, summary, linkedin = get_info()
            prompt = prompt_templates.get_system_prompt(name, summary, linkedin)
            logger.debug(f"Generated system prompt: {len(prompt)} characters")
            return prompt
        except Exception as e:
            logger.error(f"Failed to generate system prompt: {e}")
            # Fallback system prompt
            return "You are a helpful AI assistant."

    def retry_response(
        self,
        original_reply: str,
        message: str,
        history: List[Tuple[str, str]],
        feedback: str,
    ) -> Optional[str]:
        """
        Generate a single retry response based on feedback.

        Args:
            original_reply: Original response that was rejected
            message: Original user message
            history: Conversation history as Gradio tuples
            feedback: Feedback on why the response was rejected

        Returns:
            New response or None if failed
        """
        try:
            base_system_prompt = self.get_system_prompt()
            updated_system_prompt = prompt_templates.get_retry_system_prompt(
                base_system_prompt, original_reply, feedback
            )

            # Convert history to message format for retry
            history_messages = gradio_history_to_openai_messages(history)

            messages = build_retry_messages(
                updated_system_prompt, message, history_messages
            )

            logger.debug(f"Retrying response with feedback: '{feedback[:50]}...'")
            response = create_chat_completion(messages)

            if response:
                logger.debug(f"Retry response generated: {len(response)} characters")
            else:
                logger.warning("Retry response generation returned None")

            return response

        except Exception as e:
            logger.error(f"Failed to retry response: {e}")
            return None

    def retry_with_evaluation(
        self,
        original_reply: str,
        message: str,
        history: List[Tuple[str, str]],
        feedback: str,
        strategy: RetryStrategy = RetryStrategy.SINGLE,
    ) -> RetryResult:
        """
        Retry with evaluation until acceptable response or max attempts reached.

        Args:
            original_reply: Original response that was rejected
            message: Original user message
            history: Conversation history as Gradio tuples
            feedback: Initial feedback on why the response was rejected
            strategy: Retry strategy to use

        Returns:
            RetryResult with final response and metadata
        """
        start_time = time.time()
        evaluation_service = get_evaluation_service()
        attempts = [original_reply]
        current_feedback = feedback

        logger.info(f"Starting retry with strategy: {strategy.value}")

        for attempt in range(1, self.max_retries + 1):
            logger.debug(f"Retry attempt {attempt}/{self.max_retries}")

            # Generate retry response
            retry_response = self.retry_response(
                attempts[-1], message, history, current_feedback
            )

            if not retry_response:
                logger.warning(f"Retry attempt {attempt} failed to generate response")
                continue

            attempts.append(retry_response)

            # Evaluate the retry response
            evaluation = evaluation_service.evaluate_response(
                retry_response, message, history
            )

            if evaluation and evaluation.is_acceptable:
                execution_time = time.time() - start_time
                logger.info(f"Retry successful on attempt {attempt}")
                return RetryResult(
                    final_response=retry_response,
                    was_successful=True,
                    attempts_made=attempt,
                    final_evaluation=evaluation,
                    all_attempts=attempts,
                    execution_time=execution_time,
                )

            # Update feedback for next iteration if evaluation available
            if evaluation and evaluation.feedback:
                current_feedback = evaluation.feedback
                logger.debug(
                    f"Updated feedback for next attempt: {current_feedback[:50]}..."
                )

            # Apply delay before next attempt (except for last attempt)
            if attempt < self.max_retries:
                delay = min(
                    self.base_delay * (self.backoff_factor ** (attempt - 1)),
                    self.max_delay,
                )
                logger.debug(f"Waiting {delay:.1f}s before next retry attempt")
                time.sleep(delay)

        # All retries failed
        execution_time = time.time() - start_time
        final_response = attempts[-1] if len(attempts) > 1 else original_reply
        logger.warning(f"All {self.max_retries} retry attempts failed")

        return RetryResult(
            final_response=final_response,
            was_successful=False,
            attempts_made=self.max_retries,
            final_evaluation=evaluation if "evaluation" in locals() else None,
            all_attempts=attempts,
            execution_time=execution_time,
        )

    def retry_best_of_n(
        self,
        original_reply: str,
        message: str,
        history: List[Tuple[str, str]],
        feedback: str,
        n_attempts: int = 3,
    ) -> RetryResult:
        """
        Generate multiple retry responses and return the best one.

        Args:
            original_reply: Original response that was rejected
            message: Original user message
            history: Conversation history as Gradio tuples
            feedback: Feedback on why the response was rejected
            n_attempts: Number of retry attempts to generate

        Returns:
            RetryResult with the best response
        """
        start_time = time.time()
        evaluation_service = get_evaluation_service()
        attempts = [original_reply]

        logger.info(f"Generating {n_attempts} retry responses to find the best")

        # Generate multiple retry responses
        for attempt in range(1, n_attempts + 1):
            retry_response = self.retry_response(
                original_reply, message, history, feedback
            )

            if retry_response:
                attempts.append(retry_response)
                logger.debug(f"Generated retry response {attempt}/{n_attempts}")
            else:
                logger.warning(f"Failed to generate retry response {attempt}")

        # Find the best response using evaluation service
        if len(attempts) > 1:
            retry_responses = attempts[1:]  # Exclude original
            best_response, best_evaluation = evaluation_service.find_best_response(
                retry_responses, message, history
            )

            if best_response and best_evaluation and best_evaluation.is_acceptable:
                execution_time = time.time() - start_time
                logger.info(
                    f"Found acceptable response among {len(retry_responses)} retries"
                )
                return RetryResult(
                    final_response=best_response,
                    was_successful=True,
                    attempts_made=len(retry_responses),
                    final_evaluation=best_evaluation,
                    all_attempts=attempts,
                    execution_time=execution_time,
                )

        # No acceptable response found, return the best available
        execution_time = time.time() - start_time
        final_response = attempts[-1] if len(attempts) > 1 else original_reply
        logger.warning(f"No acceptable response found among {len(attempts)-1} retries")

        return RetryResult(
            final_response=final_response,
            was_successful=False,
            attempts_made=len(attempts) - 1,
            final_evaluation=None,
            all_attempts=attempts,
            execution_time=execution_time,
        )

    def retry_with_strategy(
        self,
        original_reply: str,
        message: str,
        history: List[Tuple[str, str]],
        feedback: str,
        strategy: RetryStrategy = RetryStrategy.PROGRESSIVE,
    ) -> RetryResult:
        """
        Retry using the specified strategy.

        Args:
            original_reply: Original response that was rejected
            message: Original user message
            history: Conversation history as Gradio tuples
            feedback: Feedback on why the response was rejected
            strategy: Retry strategy to use

        Returns:
            RetryResult with final response and metadata
        """
        logger.info(f"Executing retry with strategy: {strategy.value}")

        if strategy == RetryStrategy.SINGLE:
            start_time = time.time()
            retry_response = self.retry_response(
                original_reply, message, history, feedback
            )
            execution_time = time.time() - start_time

            if retry_response:
                # Evaluate the single retry
                evaluation_service = get_evaluation_service()
                evaluation = evaluation_service.evaluate_response(
                    retry_response, message, history
                )

                return RetryResult(
                    final_response=retry_response,
                    was_successful=evaluation.is_acceptable if evaluation else False,
                    attempts_made=1,
                    final_evaluation=evaluation,
                    all_attempts=[original_reply, retry_response],
                    execution_time=execution_time,
                )
            else:
                return RetryResult(
                    final_response=original_reply,
                    was_successful=False,
                    attempts_made=1,
                    all_attempts=[original_reply],
                    execution_time=execution_time,
                )

        elif strategy == RetryStrategy.MULTIPLE:
            return self.retry_with_evaluation(
                original_reply, message, history, feedback, strategy
            )

        elif strategy == RetryStrategy.PROGRESSIVE:
            return self.retry_with_evaluation(
                original_reply, message, history, feedback, strategy
            )

        elif strategy == RetryStrategy.BEST_OF_N:
            return self.retry_best_of_n(original_reply, message, history, feedback)

        else:
            raise ValueError(f"Unknown retry strategy: {strategy}")

    def get_retry_metrics(self, result: RetryResult) -> Dict[str, Any]:
        """
        Get metrics for a retry operation.

        Args:
            result: RetryResult to analyze

        Returns:
            Dictionary with retry metrics
        """
        return {
            "success_rate": 1.0 if result.was_successful else 0.0,
            "attempts_made": result.attempts_made,
            "execution_time_seconds": result.execution_time,
            "time_per_attempt": result.execution_time / max(result.attempts_made, 1),
            "total_responses_generated": len(result.all_attempts),
            "final_evaluation_score": (
                1.0
                if result.final_evaluation and result.final_evaluation.is_acceptable
                else 0.0
            ),
            "has_feedback": bool(
                result.final_evaluation and result.final_evaluation.feedback
            ),
        }

    def update_settings(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None,
    ):
        """
        Update retry service settings.

        Args:
            max_retries: New maximum number of retries
            base_delay: New base delay between retries
            max_delay: New maximum delay between retries
            backoff_factor: New exponential backoff factor
        """
        if max_retries is not None:
            self.max_retries = max_retries
            logger.debug(f"Updated max_retries to {max_retries}")

        if base_delay is not None:
            self.base_delay = base_delay
            logger.debug(f"Updated base_delay to {base_delay}")

        if max_delay is not None:
            self.max_delay = max_delay
            logger.debug(f"Updated max_delay to {max_delay}")

        if backoff_factor is not None:
            self.backoff_factor = backoff_factor
            logger.debug(f"Updated backoff_factor to {backoff_factor}")


# Global retry service instance
_retry_service: Optional[RetryService] = None


def get_retry_service() -> RetryService:
    """
    Get the global retry service instance (singleton pattern).

    Returns:
        The configured RetryService instance
    """
    global _retry_service

    if _retry_service is None:
        _retry_service = RetryService()

    return _retry_service


# Convenience functions for backward compatibility
def retry_response(
    original_reply: str,
    message: str,
    history: List[Tuple[str, str]],
    feedback: str,
) -> Optional[str]:
    """Generate a single retry response based on feedback."""
    return get_retry_service().retry_response(
        original_reply, message, history, feedback
    )


def retry_with_evaluation(
    original_reply: str,
    message: str,
    history: List[Tuple[str, str]],
    feedback: str,
    strategy: RetryStrategy = RetryStrategy.PROGRESSIVE,
) -> RetryResult:
    """Retry with evaluation until acceptable response."""
    return get_retry_service().retry_with_evaluation(
        original_reply, message, history, feedback, strategy
    )


def retry_best_of_n(
    original_reply: str,
    message: str,
    history: List[Tuple[str, str]],
    feedback: str,
    n_attempts: int = 3,
) -> RetryResult:
    """Generate multiple retry responses and return the best one."""
    return get_retry_service().retry_best_of_n(
        original_reply, message, history, feedback, n_attempts
    )
