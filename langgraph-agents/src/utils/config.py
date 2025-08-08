import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for LangGraph agents."""
    
    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model Configuration
    DEFAULT_MODEL: str = "claude-3-haiku-20240307"
    DEFAULT_TEMPERATURE: float = 0.0
    
    # Agent Configuration
    DEFAULT_MAX_ITERATIONS: int = 10
    DEFAULT_TIMEOUT: int = 30
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.ANTHROPIC_API_KEY:
            print("Warning: ANTHROPIC_API_KEY is not set. Please set it in your .env file.")
            return False
        return True

# Validate on import (but don't raise error to allow setup)
Config.validate()
