"""Configuration settings for Komodor MCP Server."""

import os
from typing import Optional

import dotenv
import structlog

logger = structlog.get_logger(__name__)


class Config:
    """Singleton configuration class for Komodor MCP Server."""

    _instance: Optional["Config"] = None
    _initialized: bool = False

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            dotenv.load_dotenv()
            self._load_config()
            Config._initialized = True

    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        # Komodor API Configuration
        self.KOMODOR_API_BASE_URL: str = os.getenv(
            "KOMODOR_API_BASE_URL", "https://api.komodor.com"
        )

        # MCP Server Configuration
        self.MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
        self.MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8002"))
        self.MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "http")
        self.KOMODOR_API_KEY: str = os.getenv("KOMODOR_API_KEY", "")
        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


# Global config instance
config = Config()
