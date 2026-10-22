from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from KBQA_* environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_prefix="KBQA_", env_file=".env", extra="ignore")

    weaviate_url: str = "http://localhost:8080"
    anthropic_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
