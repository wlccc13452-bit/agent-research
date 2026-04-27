"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / ".bot_env"),
        env_file_encoding="utf-8",
        env_prefix="CODEBUDDY_",
        extra="ignore",
    )

    # WeCom Bot Configuration
    wecom_bot_id: str
    wecom_bot_secret: str
    wecom_bot_ws_url: str = "wss://openws.work.weixin.qq.com"

    # Application Configuration
    app_name: str = "epad-bot"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8100


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
