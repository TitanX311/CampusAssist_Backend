from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Campus Assist College Service"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    GRPC_PORT: int = 50055
    AUTH_GRPC_TARGET: str = "auth-service:50051"
    COMMUNITY_SERVICE_URL: str = "http://community-service:80"

    model_config = SettingsConfigDict(
        env_file="services/college_service/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
