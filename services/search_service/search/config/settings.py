from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Campus Assist Search Service"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    DATABASE_URL: str

    # Shared JWT secret — must match auth_service
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Upstream services used by the syncer
    COLLEGE_SERVICE_URL: str = "http://college-service:80"
    COMMUNITY_SERVICE_URL: str = "http://community-service:80"

    # Background auto-sync interval in seconds (0 = disabled)
    SYNC_INTERVAL_SECONDS: int = 300  # every 5 minutes

    # Redis cache
    REDIS_URL: str = "redis://redis-service:6379/0"
    CACHE_TTL_SECONDS: int = 60  # search results cached for 60 seconds

    model_config = SettingsConfigDict(
        env_file="services/search_service/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
