from config.settings import settings
from utils.logger import logger
from config.pushover import pushover_templates
import requests

_pushover_client = None


def get_pushover_client():
    global _pushover_client
    if _pushover_client is None:
        _pushover_client = PushoverClient()
    return _pushover_client


class PushoverClient:
    def __init__(self):
        """Initialize the Pushover client with configuration."""
        if not settings.PUSHOVER_USER:
            raise ValueError("PUSHOVER_USER environment variable is required")
        if not settings.PUSHOVER_TOKEN:
            raise ValueError("PUSHOVER_TOKEN environment variable is required")

        self.user = settings.PUSHOVER_USER
        self.token = settings.PUSHOVER_TOKEN
        self.base_url = settings.PUSHOVER_BASE_URL

        logger.info("Pushover client initialized successfully")
        logger.debug(f"Pushover base URL: {self.base_url}")

    def push(self, message):
        """Send a push notification via Pushover."""
        try:
            logger.debug(f"Sending Pushover notification: '{message[:50]}...'")
            print(f"Push: {message}")

            payload = {"user": self.user, "token": self.token, "message": message}
            response = requests.post(self.base_url, data=payload)

            if response.status_code == 200:
                logger.debug("Pushover notification sent successfully")
            else:
                logger.warning(
                    f"Pushover notification failed with status {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {str(e)}")

    def record_user_details(
        self, email, name="Name not provided", notes="not provided"
    ):
        """Record user contact details via Pushover notification."""
        try:
            logger.info(f"Recording user details for: {email}")
            logger.debug(f"User details - Name: {name}, Email: {email}, Notes: {notes}")

            message = (
                f"Recording interest from {name} with email {email} and notes {notes}"
            )
            self.push(message)

            logger.debug("User details recorded successfully")
            return {"recorded": "ok"}

        except Exception as e:
            logger.error(f"Failed to record user details: {str(e)}")
            return {"error": f"Failed to record user details: {str(e)}"}

    def record_unknown_question(self, question):
        """Record an unknown question via Pushover notification."""
        try:
            logger.info(f"Recording unknown question: '{question[:50]}...'")
            logger.debug(f"Full question: {question}")

            message = f"Recording {question} asked that I couldn't answer"
            self.push(message)

            logger.debug("Unknown question recorded successfully")
            return {"recorded": "ok"}

        except Exception as e:
            logger.error(f"Failed to record unknown question: {str(e)}")
            return {"error": f"Failed to record unknown question: {str(e)}"}

    def pushover_tools(self):
        """Return the list of Pushover tools for function calling."""
        try:
            logger.debug("Loading Pushover tools definitions")
            tools = []
            tools.append(pushover_templates.get_record_user_details_json())
            tools.append(pushover_templates.get_record_unknown_question_json())

            logger.debug(f"Loaded {len(tools)} Pushover tools successfully")
            return tools

        except Exception as e:
            logger.error(f"Failed to load Pushover tools: {str(e)}")
            return []

    def execute_tool(self, tool_name: str, **kwargs) -> dict:
        """
        Execute a Pushover tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters for the tool

        Returns:
            Result of tool execution
        """
        try:
            logger.info(f"Executing Pushover tool: {tool_name}")
            logger.debug(f"Tool parameters: {kwargs}")

            if tool_name == "record_user_details":
                result = self.record_user_details(**kwargs)
                logger.debug(f"Tool execution successful: {tool_name}")
                return result

            elif tool_name == "record_unknown_question":
                result = self.record_unknown_question(**kwargs)
                logger.debug(f"Tool execution successful: {tool_name}")
                return result

            else:
                logger.error(f"Unknown Pushover tool: {tool_name}")
                raise ValueError(f"Unknown Pushover tool: {tool_name}")

        except Exception as e:
            logger.error(f"Pushover tool execution failed for {tool_name}: {str(e)}")
            return {"error": f"Tool execution failed: {str(e)}"}
