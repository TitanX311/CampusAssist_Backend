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
    APP_NAME: str = "Admin Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    # JWT (same secret as auth_service — for token verification only)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # gRPC — super-admin live check
    AUTH_GRPC_TARGET: str = "auth-service:50051"

    # Internal HTTP service base URLs (k8s ClusterIP port 80)
    AUTH_SERVICE_URL: str = "http://auth-service:80"
    COMMUNITY_SERVICE_URL: str = "http://community-service:80"
    POST_SERVICE_URL: str = "http://post-service:80"
    COMMENT_SERVICE_URL: str = "http://comment-service:80"
    ATTACHMENT_SERVICE_URL: str = "http://attachment-service:80"
    COLLEGE_SERVICE_URL: str = "http://college-service:80"


@lru_cache
def get_settings() -> Settings:
    return Settings()
