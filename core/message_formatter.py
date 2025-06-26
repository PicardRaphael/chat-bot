"""Message formatting utilities for different conversation contexts."""

from openai.types.chat import ChatCompletionMessageParam
from typing import List, Tuple
from utils.logger import logger


class MessageFormatter:
    """Handles formatting of messages for different AI conversation contexts."""

    @staticmethod
    def gradio_history_to_openai_messages(
        history: List[Tuple[str, str]],
    ) -> List[ChatCompletionMessageParam]:
        """
        Convert Gradio chat history to OpenAI message format.

        Args:
            history: List of (user_message, assistant_message) tuples from Gradio

        Returns:
            List of ChatCompletionMessageParam in OpenAI format
        """
        messages: List[ChatCompletionMessageParam] = []

        for user_msg, assistant_msg in history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})

        logger.debug(
            f"Converted {len(history)} history pairs to {len(messages)} OpenAI messages"
        )
        return messages

    @staticmethod
    def build_chat_messages(
        system_prompt: str, current_message: str, history: List[Tuple[str, str]]
    ) -> List[ChatCompletionMessageParam]:
        """
        Build complete message list for chat completion.

        Args:
            system_prompt: System prompt to set the context
            current_message: Current user message
            history: Chat history as Gradio tuples

        Returns:
            Complete list of messages for chat completion
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add history
        history_messages = MessageFormatter.gradio_history_to_openai_messages(history)
        messages.extend(history_messages)

        # Add current message
        messages.append({"role": "user", "content": current_message})

        logger.debug(
            f"Built chat messages: 1 system + {len(history_messages)} history + 1 current = {len(messages)} total"
        )
        return messages

    @staticmethod
    def build_evaluation_messages(
        system_prompt: str, user_prompt: str
    ) -> List[ChatCompletionMessageParam]:
        """
        Build messages for evaluation completion.

        Args:
            system_prompt: System prompt for the evaluator
            user_prompt: User prompt containing the content to evaluate

        Returns:
            Messages for evaluation completion
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.debug("Built evaluation messages: 1 system + 1 user = 2 total")
        return messages

    @staticmethod
    def build_retry_messages(
        updated_system_prompt: str,
        current_message: str,
        history: List[ChatCompletionMessageParam],
    ) -> List[ChatCompletionMessageParam]:
        """
        Build messages for retry completion with updated context.

        Args:
            updated_system_prompt: Updated system prompt with retry context
            current_message: Current user message to retry
            history: Previous conversation history

        Returns:
            Messages for retry completion
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": updated_system_prompt}
        ]

        # Add history (should already be in OpenAI format)
        messages.extend(history)

        # Add current message
        messages.append({"role": "user", "content": current_message})

        logger.debug(
            f"Built retry messages: 1 system + {len(history)} history + 1 current = {len(messages)} total"
        )
        return messages

    @staticmethod
    def extract_content_from_messages(
        messages: List[ChatCompletionMessageParam],
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Extract current message and history from OpenAI message format.

        Args:
            messages: List of messages in OpenAI format

        Returns:
            Tuple of (current_message, history_pairs)
        """
        history_pairs: List[Tuple[str, str]] = []
        current_message = ""

        # Skip system message (first one)
        conversation_messages = messages[1:] if len(messages) > 1 else []

        # Extract history pairs (all but the last message)
        if len(conversation_messages) > 1:
            history_messages = conversation_messages[:-1]

            # Group messages into pairs
            i = 0
            while i < len(history_messages) - 1:
                if (
                    history_messages[i]["role"] == "user"
                    and history_messages[i + 1]["role"] == "assistant"
                ):
                    # Safe content extraction
                    user_content = history_messages[i].get("content", "")
                    assistant_content = history_messages[i + 1].get("content", "")

                    # Convert to string if needed
                    user_msg = str(user_content) if user_content else ""
                    assistant_msg = str(assistant_content) if assistant_content else ""

                    history_pairs.append((user_msg, assistant_msg))
                    i += 2
                else:
                    i += 1

        # Extract current message (last one)
        if conversation_messages and conversation_messages[-1]["role"] == "user":
            current_content = conversation_messages[-1].get("content", "")
            current_message = str(current_content) if current_content else ""

        logger.debug(
            f"Extracted {len(history_pairs)} history pairs and current message from {len(messages)} messages"
        )
        return current_message, history_pairs


# Convenience functions for backward compatibility
def gradio_history_to_openai_messages(
    history: List[Tuple[str, str]],
) -> List[ChatCompletionMessageParam]:
    """Convenience function for converting Gradio history to OpenAI messages."""
    return MessageFormatter.gradio_history_to_openai_messages(history)


def build_chat_messages(
    system_prompt: str, current_message: str, history: List[Tuple[str, str]]
) -> List[ChatCompletionMessageParam]:
    """Convenience function for building chat messages."""
    return MessageFormatter.build_chat_messages(system_prompt, current_message, history)


def build_evaluation_messages(
    system_prompt: str, user_prompt: str
) -> List[ChatCompletionMessageParam]:
    """Convenience function for building evaluation messages."""
    return MessageFormatter.build_evaluation_messages(system_prompt, user_prompt)


def build_retry_messages(
    updated_system_prompt: str,
    current_message: str,
    history: List[ChatCompletionMessageParam],
) -> List[ChatCompletionMessageParam]:
    """Convenience function for building retry messages."""
    return MessageFormatter.build_retry_messages(
        updated_system_prompt, current_message, history
    )
