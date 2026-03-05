from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Campus Assist Community Service"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str

    # JWT — must match the SECRET_KEY and ALGORITHM used by auth_service
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file="services/community_service/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
