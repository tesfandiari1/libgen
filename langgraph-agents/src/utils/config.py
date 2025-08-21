import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration management for LangGraph agents. Minimal and explicit."""

    # Required
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Optional: used by integration test to choose export path
    INTEGRATION_EXPORT_PATH: str = os.getenv(
        "INTEGRATION_EXPORT_PATH", "/app/data/integration_export.csv"
    )

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration without raising to keep DX smooth."""
        if not cls.ANTHROPIC_API_KEY:
            print(
                "Warning: ANTHROPIC_API_KEY is not set. Please set it in your .env file."
            )
            return False
        return True


# Validate on import (non-fatal)
Config.validate()
