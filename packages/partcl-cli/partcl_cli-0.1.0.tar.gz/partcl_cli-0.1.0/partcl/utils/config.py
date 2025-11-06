"""
Configuration utilities for the Partcl CLI.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class PartclConfig(BaseModel):
    """Configuration for the Partcl CLI."""

    # API settings
    api_url: str = Field(
        default="https://partcl--boson-eda-processor-web.modal.run",
        description="Base URL for the API server",
    )
    local_url: str = Field(
        default="http://localhost:8000",
        description="URL for local Docker server",
    )
    use_local: bool = Field(
        default=False,
        description="Use local server by default",
    )

    # Authentication
    token: Optional[str] = Field(
        default=None,
        description="JWT authentication token",
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="JWT refresh token for renewing sessions",
    )

    # Output preferences
    output_format: str = Field(
        default="table",
        description="Default output format (json or table)",
    )

    # Request settings
    timeout: int = Field(
        default=300,
        description="Default request timeout in seconds",
    )

    @classmethod
    def from_env(cls) -> "PartclConfig":
        """
        Create configuration from environment variables.

        Environment variables:
        - PARTCL_API_URL: Override API URL
        - PARTCL_LOCAL_URL: Override local server URL
        - PARTCL_LOCAL: Set to "true" to use local mode by default
        - PARTCL_TOKEN: JWT authentication token
        - PARTCL_REFRESH_TOKEN: JWT refresh token
        - PARTCL_OUTPUT_FORMAT: Default output format
        - PARTCL_TIMEOUT: Request timeout
        """
        return cls(
            api_url=os.getenv("PARTCL_API_URL", cls.__fields__["api_url"].default),
            local_url=os.getenv("PARTCL_LOCAL_URL", cls.__fields__["local_url"].default),
            use_local=os.getenv("PARTCL_LOCAL", "false").lower() == "true",
            token=os.getenv("PARTCL_TOKEN"),
            refresh_token=os.getenv("PARTCL_REFRESH_TOKEN"),
            output_format=os.getenv(
                "PARTCL_OUTPUT_FORMAT", cls.__fields__["output_format"].default
            ),
            timeout=int(os.getenv("PARTCL_TIMEOUT", cls.__fields__["timeout"].default)),
        )

    @classmethod
    def load(cls) -> "PartclConfig":
        """
        Load configuration from environment and config files.

        Checks for .partcl.env in:
        1. Current directory
        2. Home directory

        Returns:
            PartclConfig instance
        """
        # Load from .partcl.env files if they exist
        config_paths = [
            Path.cwd() / ".partcl.env",
            Path.home() / ".partcl.env",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    from dotenv import load_dotenv

                    load_dotenv(config_path)
                except ImportError:
                    pass  # python-dotenv not installed

        # Create config from environment
        return cls.from_env()

    def get_base_url(self, use_local: Optional[bool] = None) -> str:
        """
        Get the appropriate base URL.

        Args:
            use_local: Override local mode setting

        Returns:
            Base URL for API requests
        """
        if use_local is None:
            use_local = self.use_local

        return self.local_url if use_local else self.api_url