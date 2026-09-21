"""Application configuration loader."""

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class AppSettings(BaseSettings):
    """Type-safe application settings."""

    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "devops-monitored-app"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    METRICS_ENABLED: bool = True


@lru_cache
def get_settings() -> AppSettings:
    """Return cached application settings singleton."""
    return AppSettings()
