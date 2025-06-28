"""Tools service for managing external function calling tools."""

import json
from typing import List, Dict, Any, Optional
from utils.logger import logger
from api.pushover_client import get_pushover_client


class ToolsService:
    """Service for managing and orchestrating external function calling tools."""

    def __init__(self):
        """Initialize the tools service."""
        self.pushover_client = get_pushover_client()
        logger.debug("ToolsService initialized")

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools for function calling.

        Returns:
            List of tool definitions for LLM function calling
        """
        tools = []

        # Add Pushover tools (delegate to client)
        try:
            pushover_tools = self.pushover_client.pushover_tools()
            tools.extend(pushover_tools)
            logger.debug(f"Added {len(pushover_tools)} Pushover tools")
        except Exception as e:
            logger.warning(f"Failed to load Pushover tools: {e}")

        # Future tools can be added here:
        # tools.extend(self.slack_client.slack_tools())
        # tools.extend(self.email_client.email_tools())

        logger.info(f"Loaded {len(tools)} total tools")
        return tools

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters for the tool

        Returns:
            Result of tool execution
        """
        try:
            logger.info(f"Executing tool: {tool_name}")

            # Route to appropriate client based on tool name
            if tool_name in ["record_user_details", "record_unknown_question"]:
                return self.pushover_client.execute_tool(tool_name, **kwargs)

            # Future tools routing:
            # elif tool_name.startswith("slack_"):
            #     return self.slack_client.execute_tool(tool_name, **kwargs)

            else:
                logger.error(f"Unknown tool: {tool_name}")
                return {"error": f"Tool '{tool_name}' not found"}

        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get tools filtered by category.

        Args:
            category: Category to filter by (e.g., 'notification', 'communication')

        Returns:
            List of tools in the specified category
        """
        all_tools = self.get_all_tools()

        # Simple category mapping (can be enhanced)
        category_mapping = {
            "notification": ["record_user_details", "record_unknown_question"],
            "communication": ["record_user_details"],
            "monitoring": ["record_unknown_question"],
        }

        if category not in category_mapping:
            return []

        return [
            tool for tool in all_tools if tool.get("name") in category_mapping[category]
        ]

    def is_tool_available(self, tool_name: str) -> bool:
        """
        Check if a tool is available.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is available, False otherwise
        """
        all_tools = self.get_all_tools()
        return any(tool.get("name") == tool_name for tool in all_tools)


# Global tools service instance
_tools_service: Optional[ToolsService] = None


def get_tools_service() -> ToolsService:
    """
    Get the global tools service instance (singleton pattern).

    Returns:
        The configured ToolsService instance
    """
    global _tools_service

    if _tools_service is None:
        _tools_service = ToolsService()

    return _tools_service


# Convenience functions
def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available tools."""
    return get_tools_service().get_all_tools()


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool by name."""
    return get_tools_service().execute_tool(tool_name, **kwargs)


def handle_tool_calls(tool_calls) -> List[Dict[str, Any]]:
    """
    Handle OpenAI function calling tool calls.

    Args:
        tool_calls: List of tool calls from OpenAI API

    Returns:
        List of tool results in OpenAI format
    """
    results = []

    for tool_call in tool_calls:
        try:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            logger.info(f"Tool called: {tool_name}")
            print(f"Tool called: {tool_name}", flush=True)

            # Use ToolsService to execute the tool
            result = get_tools_service().execute_tool(tool_name, **arguments)

            # Format result for OpenAI
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )

        except Exception as e:
            logger.error(f"Failed to handle tool call {tool_call.id}: {e}")

            # Error response in OpenAI format
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(
                        {"error": f"Tool execution failed: {str(e)}"}
                    ),
                    "tool_call_id": tool_call.id,
                }
            )

    return results
