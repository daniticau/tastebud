from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables."""

    database_url: str
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    fuzzy_match_threshold: float = 0.6
    recency_halflife_days: int = 30
    min_reviews_for_ranking: int = 1

    model_config = {"env_prefix": "TASTEBUD_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    """Lazy singleton — only validates env vars on first call."""
    return Settings()
