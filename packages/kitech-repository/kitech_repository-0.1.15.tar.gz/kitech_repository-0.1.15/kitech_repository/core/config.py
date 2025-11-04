"""Configuration management for KITECH Repository."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration settings for KITECH Repository.

    Environment variables can be used with KITECH_ prefix:
    - KITECH_SERVER_URL: Server URL (default: http://localhost:6300)
    - KITECH_CHUNK_SIZE: Download chunk size in bytes (default: 8192)
    """

    model_config = ConfigDict(env_prefix="KITECH_", populate_by_name=True)

    server_url: str = Field(
        default=os.getenv("KITECH_SERVER_URL") or os.getenv("KITECH_API_BASE_URL", "http://localhost:6300"),
        description="Server URL for KITECH API (without version)",
        alias="api_base_url",  # Backward compatibility
    )

    @model_validator(mode="after")
    def normalize_server_url(self) -> "Config":
        """
        Normalize Server URL:
        1. Add http:// if no protocol specified
        2. Remove trailing slashes
        3. Add /service-api if not already present (nginx prefix)
        """
        url = self.server_url

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"

        # Remove trailing slashes first
        url = url.rstrip("/")

        # Add /service-api if not already present (nginx prefix requirement)
        if not url.endswith("/service-api"):
            url = f"{url}/service-api"

        self.server_url = url
        return self

    chunk_size: int = Field(
        default=int(os.getenv("KITECH_CHUNK_SIZE", "8192")),
        description="Chunk size for file downloads in bytes",
    )

    # Runtime-only properties (not saved to config.json)
    @property
    def config_dir(self) -> Path:
        """Directory for storing configuration files."""
        return Path.home() / ".kitech"

    @property
    def download_dir(self) -> Path:
        """Default directory for downloads."""
        return Path.cwd() / "downloads"

    @property
    def api_token(self) -> str | None:
        """API token - managed by AuthManager, not stored in config."""
        return None

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / "config.json"
        config_file.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file or environment."""
        config_dir = Path.home() / ".kitech"
        config_file = config_dir / "config.json"

        if config_file.exists():
            import json

            data = json.loads(config_file.read_text())
            return cls(**data)

        return cls()


def get_config() -> Config:
    """Get the current configuration."""
    return Config.load()
