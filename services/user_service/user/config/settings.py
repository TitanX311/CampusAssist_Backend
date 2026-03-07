from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "User Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str

    # JWT (same secret as auth-service to verify tokens)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Downstream gRPC
    AUTH_GRPC_TARGET: str = "auth-service:50051"

    # Downstream HTTP (cluster-internal, not via ingress)
    AUTH_SERVICE_URL: str = "http://auth-service:80"
    POST_SERVICE_URL: str = "http://post-service"
    COMMENT_SERVICE_URL: str = "http://comment-service"
    COMMUNITY_SERVICE_URL: str = "http://community-service"

    # How long (seconds) cached stats remain valid before a refresh is forced
    STATS_CACHE_TTL_SECONDS: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
