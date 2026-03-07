from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Campus Assist Notification Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8006

    # Database (notifications are persisted for ACID durability)
    DATABASE_URL: str

    # JWT — same secret as auth_service, verified locally without a network hop
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # gRPC port this service listens on (other services push notifications here)
    GRPC_PORT: int = 50056


@lru_cache
def get_settings() -> Settings:
    return Settings()
