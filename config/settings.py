"""Configuration settings for the chatbot."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


class Settings:
    """Application settings with environment variable support."""

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    PUSHOVER_USER: str = os.getenv("PUSHOVER_USER", "")
    PUSHOVER_TOKEN: str = os.getenv("PUSHOVER_TOKEN", "")

    # API URLs
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    PUSHOVER_BASE_URL: str = "https://api.pushover.net/1/messages.json"

    # Model Settings
    CHAT_MODEL: str = "gpt-4o-mini"
    EVALUATION_MODEL: str = "gemini-2.0-flash"

    # Chat AI Response Parameters
    CHAT_TEMPERATURE: float = 0.4
    CHAT_TOP_P: float = 0.95
    CHAT_FREQUENCY_PENALTY: float = 0.3
    CHAT_PRESENCE_PENALTY: float = 0.2
    CHAT_MAX_TOKENS: int = 600

    # Evaluation AI Response Parameters
    EVAL_TEMPERATURE: float = 0.4
    EVAL_TOP_P: float = 0.95
    EVAL_FREQUENCY_PENALTY: float = 0.3
    EVAL_PRESENCE_PENALTY: float = 0.2
    EVAL_MAX_TOKENS: int = 600

    # File Paths
    PROFILE_DIR: str = "files"
    LINKEDIN_PDF: str = "linkedin.pdf"
    SUMMARY_TXT: str = "summary.txt"

    # Chat Settings
    MAX_RETRIES: int = 3
    ENABLE_EVALUATION: bool = True

    # UI Settings
    APP_TITLE: str = "Raphaël PICARD"
    THEME: str = "soft"

    # Logging
    LOG_LEVEL: str = "INFO"


# Global settings instance
settings = Settings()
