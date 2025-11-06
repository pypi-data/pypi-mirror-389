"""Configuration management for Volcengine Video MCP Server."""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for Volcengine Video MCP Server."""

    # Server metadata
    SERVER_NAME: Final[str] = "volcengine-video-mcp"
    SERVER_VERSION: Final[str] = "0.1.0"

    # API Configuration
    ARK_API_KEY: Final[str] = os.getenv("ARK_API_KEY", "")
    ARK_BASE_URL: Final[str] = os.getenv(
        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com"
    )

    # API Endpoints
    API_VERSION: Final[str] = "v3"
    TASKS_ENDPOINT: Final[str] = f"/api/{API_VERSION}/contents/generations/tasks"

    # Supported Models
    SUPPORTED_MODELS: Final[dict[str, str]] = {
        "doubao-seedance-1-0-pro": "doubao-seedance-1-0-pro-250528",
        "doubao-seedance-1-0-pro-fast": "doubao-seedance-1-0-pro-fast-250528",
        "doubao-seedance-1-0-lite-t2v": "doubao-seedance-1-0-lite-t2v-250528",
        "doubao-seedance-1-0-lite-i2v": "doubao-seedance-1-0-lite-i2v-250528",
        "wan2-1-14b-t2v": "wan2-1-14b-t2v",
        "wan2-1-14b-i2v": "wan2-1-14b-i2v",
        "wan2-1-14b-flf2v": "wan2-1-14b-flf2v",
    }

    # Default Parameters
    DEFAULT_RESOLUTION: Final[str] = "720p"
    DEFAULT_RATIO: Final[str] = "16:9"
    DEFAULT_DURATION: Final[int] = 5
    DEFAULT_FPS: Final[int] = 24
    DEFAULT_SEED: Final[int] = -1

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.ARK_API_KEY:
            raise ValueError("ARK_API_KEY environment variable is required")

    @classmethod
    def get_full_url(cls, endpoint: str) -> str:
        """Get full URL for an endpoint."""
        return f"{cls.ARK_BASE_URL}{endpoint}"
