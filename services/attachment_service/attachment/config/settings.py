from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Campus Assist Attachment Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    # Database
    DATABASE_URL: str

    # JWT — shared with auth_service
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # MinIO / object storage
    MINIO_ENDPOINT: str = "minio-service:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "campus-assist"
    MINIO_SECURE: bool = False

    # gRPC server
    GRPC_PORT: int = 50054

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = {
        "env_file": "services/attachment_service/.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
