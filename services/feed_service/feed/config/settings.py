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
    APP_NAME: str = "Feed Service"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database (feed_interactions — ACID-compliant seen tracking)
    DATABASE_URL: str

    # JWT (same secret as auth-service to verify tokens without an extra gRPC hop)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Redis (shared with other services — uses its own key prefix)
    REDIS_URL: str = "redis://redis:6379/0"

    # Downstream HTTP (cluster-internal)
    COMMUNITY_SERVICE_URL: str = "http://community-service"
    POST_SERVICE_URL: str = "http://post-service"

    # Feed cache TTL in seconds (default 5 min; override to 2 min in dev)
    FEED_CACHE_TTL_SECONDS: int = 300

    # How many hours of posts to include in the feed window (default 7 days)
    FEED_WINDOW_HOURS: int = 168

    # Maximum posts to fetch per community when building the feed
    FEED_POSTS_PER_COMMUNITY: int = 100

    # Posts newer than this are placed in the "recent" section (newest-first).
    # Posts older than this are placed in the "popular" section (likes-first).
    FEED_RECENT_WINDOW_HOURS: int = 24

    # ---------------------------------------------------------------------------
    # Across-India feed (public communities, engagement-ranked discovery feed)
    # ---------------------------------------------------------------------------

    # Shared Redis TTL — longer than my-feed because it's not per-user (10 min)
    INDIA_FEED_CACHE_TTL_SECONDS: int = 600

    # How far back to look for trending posts (7 days — wide net for viral content)
    INDIA_FEED_WINDOW_HOURS: int = 168

    # Max posts returned by post_service in a single trending-posts query
    INDIA_FEED_TOP_N: int = 200

    # Minimum engagement score a post must have to appear in the India feed.
    # Keeps truly-zero-engagement posts off the discovery surface.
    # score = likes*5 + comments*3; default=5 means at least ~1 like.
    INDIA_FEED_MIN_ENGAGEMENT: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
