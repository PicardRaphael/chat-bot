"""Chat service for handling conversation logic."""

from typing import List, Tuple, Optional
from config.prompts import prompt_templates
from utils.logger import logger, EvaluationLogContext
from core.models import Evaluation, ChatRequest, ChatResponse
from core.message_formatter import build_chat_messages, build_retry_messages
from core.profile_loader import get_info
from api.openai_client import create_chat_completion
from services.evaluation_service import get_evaluation_service
from services.retry_service import get_retry_service
from services.tools_service import get_all_tools


class ChatService:
    """Service for handling chat conversations with evaluation and retry logic."""

    def __init__(self):
        """Initialize the chat service."""
        logger.debug("ChatService initialized")

    def get_system_prompt(self) -> str:
        """
        Generate the system prompt for chat based on user profile.

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

    def generate_response(
        self, message: str, history: List[Tuple[str, str]]
    ) -> Optional[str]:
        """
        Generate a response to the user message.

        Args:
            message: User message
            history: Conversation history as Gradio tuples

        Returns:
            Generated response or None if failed
        """
        try:
            system_prompt = self.get_system_prompt()
            messages = build_chat_messages(system_prompt, message, history)
            tools = get_all_tools()

            logger.debug(f"Generating response for message: '{message[:50]}...'")
            response = create_chat_completion(messages, tools=tools)

            if response:
                logger.debug(f"Response generated: {len(response)} characters")
            else:
                logger.warning("Response generation returned None")

            return response

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return None

    def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a complete chat request with evaluation and retry logic.

        Args:
            request: ChatRequest object containing message and history

        Returns:
            ChatResponse object with the final response and metadata
        """
        eval_context = EvaluationLogContext(request.message)

        try:
            # Generate initial response
            response = self.generate_response(request.message, request.history)
            reply = response or "Sorry, I couldn't generate a response."

            # Evaluate the response
            eval_context.log_evaluation_start()
            evaluation_service = get_evaluation_service()
            evaluation = evaluation_service.evaluate_response(
                reply, request.message, request.history
            )

            was_retried = False

            if evaluation and evaluation.is_acceptable:
                eval_context.log_evaluation_passed()
                logger.info("Response accepted by evaluator")

            elif evaluation:
                eval_context.log_evaluation_failed(evaluation.feedback)
                logger.info(
                    f"Response rejected, retrying with feedback: {evaluation.feedback}"
                )

                # Retry with feedback using RetryService
                retry_service = get_retry_service()
                retry_result = retry_service.retry_with_strategy(
                    reply, request.message, request.history, evaluation.feedback
                )

                if retry_result.was_successful:
                    reply = retry_result.final_response
                    was_retried = True
                    logger.info(
                        f"Retry successful after {retry_result.attempts_made} attempts"
                    )
                else:
                    logger.warning(
                        f"Retry failed after {retry_result.attempts_made} attempts, keeping original response"
                    )

            else:
                eval_context.log_evaluation_error("Evaluation service returned None")
                logger.warning("Evaluation failed, keeping original response")

            return ChatResponse(
                content=reply, evaluation=evaluation, was_retried=was_retried
            )

        except Exception as e:
            logger.error(f"Failed to process chat request: {e}")
            eval_context.log_evaluation_error(f"Chat processing error: {e}")

            return ChatResponse(
                content="Sorry, I encountered an error while processing your request.",
                evaluation=None,
                was_retried=False,
            )

    def chat(self, message: str, history: List[Tuple[str, str]]) -> str:
        """
        Simple chat interface (for backward compatibility with Gradio).

        Args:
            message: User message
            history: Conversation history as Gradio tuples

        Returns:
            Response string
        """
        request = ChatRequest(message=message, history=history)
        response = self.process_chat_request(request)
        return response.content


# Global chat service instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    Get the global chat service instance (singleton pattern).

    Returns:
        The configured ChatService instance
    """
    global _chat_service

    if _chat_service is None:
        _chat_service = ChatService()

    return _chat_service


# Convenience functions for backward compatibility
def chat(message: str, history: List[Tuple[str, str]]) -> str:
    """Process a chat message and return response."""
    return get_chat_service().chat(message, history)


def generate_response(message: str, history: List[Tuple[str, str]]) -> Optional[str]:
    """Generate a response to the user message."""
    return get_chat_service().generate_response(message, history)


def evaluate_response(
    reply: str, message: str, history: List[Tuple[str, str]]
) -> Optional[Evaluation]:
    """Evaluate a response for quality."""
    return get_evaluation_service().evaluate_response(reply, message, history)
