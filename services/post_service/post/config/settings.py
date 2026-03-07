from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Campus Assist Post Service"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    DATABASE_URL: str

    # JWT — must match the SECRET_KEY and ALGORITHM used by auth_service
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Internal service URLs
    COMMUNITY_SERVICE_URL: str = "http://community-service:80"

    # gRPC
    GRPC_PORT: int = 50053
    COMMUNITY_GRPC_TARGET: str = "community-service:50052"
    ATTACHMENT_GRPC_TARGET: str = "attachment-service:50054"
    AUTH_GRPC_TARGET: str = "auth-service:50051"
    NOTIFICATION_GRPC_TARGET: str = "notification-service:50056"

    model_config = SettingsConfigDict(
        env_file="services/post_service/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
