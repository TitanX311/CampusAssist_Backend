from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Campus Assist Comment Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8003

    # Database
    DATABASE_URL: str

    # JWT — shared with auth_service
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Internal service URLs (kept for reference / non-gRPC paths)
    COMMUNITY_SERVICE_URL: str = "http://community-service:80"
    POST_SERVICE_URL: str = "http://post-service:80"

    # gRPC targets
    COMMUNITY_GRPC_TARGET: str = "community-service:50052"
    POST_GRPC_TARGET: str = "post-service:50053"
    AUTH_GRPC_TARGET: str = "auth-service:50051"
    NOTIFICATION_GRPC_TARGET: str = "notification-service:50056"

    model_config = {
        "env_file": "services/comment_service/.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
