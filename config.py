"""Application configuration for MAXY."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Environment-backed settings. Variables use the MAXY_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="MAXY_",
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "INFO"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:1b"
    database_path: str = str(ROOT_DIR / "data" / "maxy.db")
    max_history_messages: int = 12
    request_timeout_seconds: float = 90.0


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
