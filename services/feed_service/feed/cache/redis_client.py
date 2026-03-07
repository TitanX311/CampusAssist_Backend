"""
Redis cache layer for the feed service.

Key layout (all keys prefixed with ``feed:v1:``):
  feed:v1:{user_id}       — JSON-serialised list of scored FeedItem dicts.
                            TTL = FEED_CACHE_TTL_SECONDS (default 5 min).
  feed:v1:{user_id}:seen  — Redis Set of post_ids the user has seen.
                            TTL = 7 days (rolling; refreshed on each write).
  feed:v1:india           — Shared JSON list for the Across-India trending feed.
                            TTL = INDIA_FEED_CACHE_TTL_SECONDS (default 10 min).
                            Not per-user — one cached list for everyone.

Design notes:
  - Redis is the *fast path* — reads are O(1).
  - Postgres (FeedInteraction table) is the *durable* store; it survives
    Redis flushes and is the source of truth for "seen" state on fresh builds.
  - The seen set TTL is rolling: each ``mark_seen`` call resets the 7-day clock
    so active users never lose their seen history.
  - The India feed cache is shared across all users. It is rebuilt on the first
    request after the TTL expires (or after an explicit invalidation).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from feed.config.settings import get_settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

_FEED_KEY = "feed:v1:{user_id}"
_SEEN_KEY = "feed:v1:{user_id}:seen"
_INDIA_FEED_KEY = "feed:v1:india"
_SEEN_TTL_SECONDS = 604_800  # 7 days


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis


# ---------------------------------------------------------------------------
# Feed cache
# ---------------------------------------------------------------------------

async def get_cached_feed(user_id: str) -> list[dict[str, Any]] | None:
    """Return the cached feed for *user_id*, or ``None`` on cache miss."""
    r = _get_redis()
    try:
        raw = await r.get(_FEED_KEY.format(user_id=user_id))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis get_cached_feed error for %s: %s", user_id, exc)
        return None


async def set_cached_feed(
    user_id: str,
    items: list[dict[str, Any]],
    ttl: int,
) -> None:
    """Store the feed list in Redis with the given TTL (seconds)."""
    r = _get_redis()
    try:
        await r.set(
            _FEED_KEY.format(user_id=user_id),
            json.dumps(items),
            ex=ttl,
        )
    except Exception as exc:
        logger.warning("Redis set_cached_feed error for %s: %s", user_id, exc)


async def invalidate_feed(user_id: str) -> None:
    """Delete the cached feed so the next request triggers a fresh build."""
    r = _get_redis()
    try:
        await r.delete(_FEED_KEY.format(user_id=user_id))
    except Exception as exc:
        logger.warning("Redis invalidate_feed error for %s: %s", user_id, exc)


# ---------------------------------------------------------------------------
# Seen set
# ---------------------------------------------------------------------------

async def mark_seen(user_id: str, post_id: str) -> None:
    """Add *post_id* to the user's seen set and reset its 7-day TTL."""
    r = _get_redis()
    try:
        key = _SEEN_KEY.format(user_id=user_id)
        await r.sadd(key, post_id)
        await r.expire(key, _SEEN_TTL_SECONDS)
    except Exception as exc:
        logger.warning("Redis mark_seen error for %s / %s: %s", user_id, post_id, exc)


async def mark_seen_bulk(user_id: str, post_ids: list[str]) -> None:
    """Add multiple *post_ids* to the seen set in a single pipeline call."""
    if not post_ids:
        return
    r = _get_redis()
    try:
        key = _SEEN_KEY.format(user_id=user_id)
        pipe = r.pipeline()
        pipe.sadd(key, *post_ids)
        pipe.expire(key, _SEEN_TTL_SECONDS)
        await pipe.execute()
    except Exception as exc:
        logger.warning("Redis mark_seen_bulk error for %s: %s", user_id, exc)


async def get_seen_ids(user_id: str) -> set[str]:
    """Return the set of post_ids the user has already seen (from Redis)."""
    r = _get_redis()
    try:
        members = await r.smembers(_SEEN_KEY.format(user_id=user_id))
        return set(members)
    except Exception as exc:
        logger.warning("Redis get_seen_ids error for %s: %s", user_id, exc)
        return set()


# ---------------------------------------------------------------------------
# India (Across-India) feed cache — shared, not per-user
# ---------------------------------------------------------------------------

async def get_cached_india_feed() -> list[dict[str, Any]] | None:
    """Return the shared Across-India trending feed, or ``None`` on cache miss."""
    r = _get_redis()
    try:
        raw = await r.get(_INDIA_FEED_KEY)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis get_cached_india_feed error: %s", exc)
        return None


async def set_cached_india_feed(items: list[dict[str, Any]], ttl: int) -> None:
    """Store the India feed list in Redis with the given TTL (seconds)."""
    r = _get_redis()
    try:
        await r.set(_INDIA_FEED_KEY, json.dumps(items), ex=ttl)
    except Exception as exc:
        logger.warning("Redis set_cached_india_feed error: %s", exc)


async def invalidate_india_feed() -> None:
    """Delete the shared India feed cache to force a rebuild on next request."""
    r = _get_redis()
    try:
        await r.delete(_INDIA_FEED_KEY)
    except Exception as exc:
        logger.warning("Redis invalidate_india_feed error: %s", exc)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

async def close() -> None:
    """Close the Redis connection pool on shutdown."""
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception:
            pass
        _redis = None
