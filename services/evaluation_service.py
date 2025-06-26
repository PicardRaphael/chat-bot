"""Evaluation service for response quality assessment."""

from typing import List, Tuple, Optional
from config.prompts import prompt_templates
from utils.logger import logger
from core.models import Evaluation
from core.message_formatter import gradio_history_to_openai_messages
from core.profile_loader import get_info
from api.gemini_client import create_evaluation_completion


class EvaluationService:
    """Service for evaluating response quality and appropriateness."""

    def __init__(self):
        """Initialize the evaluation service."""
        logger.debug("EvaluationService initialized")

    def get_evaluator_system_prompt(self) -> str:
        """
        Generate the evaluator system prompt based on user profile.

        Returns:
            Evaluator system prompt string
        """
        try:
            name, summary, linkedin = get_info()
            prompt = prompt_templates.get_evaluator_system_prompt(
                name, summary, linkedin
            )
            logger.debug(f"Generated evaluator system prompt: {len(prompt)} characters")
            return prompt
        except Exception as e:
            logger.error(f"Failed to generate evaluator system prompt: {e}")
            # Fallback evaluator prompt
            return "You are an AI assistant that evaluates responses for quality and appropriateness."

    def evaluate_response(
        self, reply: str, message: str, history: List[Tuple[str, str]]
    ) -> Optional[Evaluation]:
        """
        Evaluate a response for quality and appropriateness.

        Args:
            reply: Response to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples

        Returns:
            Evaluation object or None if failed
        """
        try:
            # Convert history to proper format for evaluation
            history_messages = gradio_history_to_openai_messages(history)

            system_prompt = self.get_evaluator_system_prompt()
            user_prompt = prompt_templates.get_evaluator_user_prompt(
                reply, message, history_messages
            )

            logger.debug(f"Evaluating response: '{reply[:50]}...'")
            evaluation = create_evaluation_completion(system_prompt, user_prompt)

            if evaluation:
                logger.debug(
                    f"Evaluation completed: acceptable={evaluation.is_acceptable}"
                )
                if evaluation.is_acceptable:
                    logger.info("Response accepted by evaluator")
                else:
                    logger.info(f"Response rejected: {evaluation.feedback}")
            else:
                logger.warning("Evaluation returned None")

            return evaluation

        except Exception as e:
            logger.error(f"Failed to evaluate response: {e}")
            return None

    def evaluate_multiple_responses(
        self, responses: List[str], message: str, history: List[Tuple[str, str]]
    ) -> List[Optional[Evaluation]]:
        """
        Evaluate multiple responses and return their evaluations.

        Args:
            responses: List of responses to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples

        Returns:
            List of Evaluation objects (or None for failed evaluations)
        """
        evaluations = []

        logger.debug(f"Evaluating {len(responses)} responses")

        for i, response in enumerate(responses):
            logger.debug(f"Evaluating response {i+1}/{len(responses)}")
            evaluation = self.evaluate_response(response, message, history)
            evaluations.append(evaluation)

        # Log summary
        accepted_count = sum(1 for eval in evaluations if eval and eval.is_acceptable)
        logger.info(
            f"Evaluation summary: {accepted_count}/{len(responses)} responses accepted"
        )

        return evaluations

    def find_best_response(
        self, responses: List[str], message: str, history: List[Tuple[str, str]]
    ) -> Tuple[Optional[str], Optional[Evaluation]]:
        """
        Evaluate multiple responses and return the best one.

        Args:
            responses: List of responses to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples

        Returns:
            Tuple of (best_response, its_evaluation) or (None, None) if no acceptable response
        """
        if not responses:
            logger.warning("No responses provided for evaluation")
            return None, None

        evaluations = self.evaluate_multiple_responses(responses, message, history)

        # Find the first acceptable response
        for response, evaluation in zip(responses, evaluations):
            if evaluation and evaluation.is_acceptable:
                logger.info(f"Found acceptable response: '{response[:50]}...'")
                return response, evaluation

        # If no acceptable response, return the first one with its evaluation
        logger.warning("No acceptable responses found, returning first response")
        return responses[0], evaluations[0] if evaluations else None

    def is_response_acceptable(
        self, reply: str, message: str, history: List[Tuple[str, str]]
    ) -> bool:
        """
        Quick check if a response is acceptable.

        Args:
            reply: Response to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples

        Returns:
            True if response is acceptable, False otherwise
        """
        evaluation = self.evaluate_response(reply, message, history)
        return evaluation is not None and evaluation.is_acceptable

    def get_evaluation_feedback(
        self, reply: str, message: str, history: List[Tuple[str, str]]
    ) -> Optional[str]:
        """
        Get feedback on why a response was rejected.

        Args:
            reply: Response to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples

        Returns:
            Feedback string or None if evaluation failed
        """
        evaluation = self.evaluate_response(reply, message, history)
        if evaluation:
            return evaluation.feedback
        return None

    def evaluate_with_custom_prompt(
        self,
        reply: str,
        message: str,
        history: List[Tuple[str, str]],
        custom_system_prompt: str,
    ) -> Optional[Evaluation]:
        """
        Evaluate a response with a custom system prompt.

        Args:
            reply: Response to evaluate
            message: Original user message
            history: Conversation history as Gradio tuples
            custom_system_prompt: Custom system prompt for evaluation

        Returns:
            Evaluation object or None if failed
        """
        try:
            # Convert history to proper format for evaluation
            history_messages = gradio_history_to_openai_messages(history)

            user_prompt = prompt_templates.get_evaluator_user_prompt(
                reply, message, history_messages
            )

            logger.debug(f"Evaluating with custom prompt: '{reply[:50]}...'")
            evaluation = create_evaluation_completion(custom_system_prompt, user_prompt)

            if evaluation:
                logger.debug(
                    f"Custom evaluation completed: acceptable={evaluation.is_acceptable}"
                )
            else:
                logger.warning("Custom evaluation returned None")

            return evaluation

        except Exception as e:
            logger.error(f"Failed to evaluate with custom prompt: {e}")
            return None


# Global evaluation service instance
_evaluation_service: Optional[EvaluationService] = None


def get_evaluation_service() -> EvaluationService:
    """
    Get the global evaluation service instance (singleton pattern).

    Returns:
        The configured EvaluationService instance
    """
    global _evaluation_service

    if _evaluation_service is None:
        _evaluation_service = EvaluationService()

    return _evaluation_service


# Convenience functions for backward compatibility
def evaluate_response(
    reply: str, message: str, history: List[Tuple[str, str]]
) -> Optional[Evaluation]:
    """Evaluate a response for quality."""
    return get_evaluation_service().evaluate_response(reply, message, history)


def is_response_acceptable(
    reply: str, message: str, history: List[Tuple[str, str]]
) -> bool:
    """Quick check if a response is acceptable."""
    return get_evaluation_service().is_response_acceptable(reply, message, history)


def get_evaluation_feedback(
    reply: str, message: str, history: List[Tuple[str, str]]
) -> Optional[str]:
    """Get feedback on why a response was rejected."""
    return get_evaluation_service().get_evaluation_feedback(reply, message, history)


def find_best_response(
    responses: List[str], message: str, history: List[Tuple[str, str]]
) -> Tuple[Optional[str], Optional[Evaluation]]:
    """Evaluate multiple responses and return the best one."""
    return get_evaluation_service().find_best_response(responses, message, history)
