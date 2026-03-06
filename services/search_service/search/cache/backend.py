"""
Redis-backed search result cache.

Key design
----------
  Prefix : "search:"
  Key    : search:<md5(q|type|college_id|page|page_size)>
  Value  : JSON-encoded {"items": [...], "total": N}
  TTL    : CACHE_TTL_SECONDS (default 60s)

Revalidation policy
-------------------
1. Time-based   — keys naturally expire after TTL seconds.
2. Event-based  — invalidate() is called after every sync (background loop
                  AND manual POST /api/search/sync).
                  Uses SCAN+DEL on "search:*" so we never accidentally
                  flush unrelated keyspaces.

Graceful degradation
--------------------
If Redis is unavailable every method silently returns a safe fallback
so search queries still hit PostgreSQL without raising an error.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Module-level singleton — initialised once in app lifespan.
_redis: aioredis.Redis | None = None


# ── Lifecycle ────────────────────────────────────────────────────────────────

async def init_cache(redis_url: str) -> None:
    """Open a connection pool and verify connectivity. Called once at startup."""
    global _redis
    _redis = aioredis.from_url(redis_url, decode_responses=True)
    await _redis.ping()
    logger.info("Redis cache connected: %s", redis_url)


async def close_cache() -> None:
    """Close the connection pool gracefully. Called on shutdown."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_cache() -> SearchCache:
    """Return a SearchCache instance bound to the current Redis connection."""
    return SearchCache(_redis)


# ── Cache class ──────────────────────────────────────────────────────────────

class SearchCache:
    PREFIX = "search:"

    def __init__(self, client: aioredis.Redis | None) -> None:
        self._r = client

    # ── Key ──────────────────────────────────────────────────────────────────

    def _key(
        self, q: str, type_: str, college_id: str | None, page: int, page_size: int
    ) -> str:
        """
        Stable, case-folded cache key.

        Lowercasing + stripping collapses "  IIT  " and "iit" to the same
        bucket so we don't store duplicates for the same logical query.
        """
        raw = f"{q.lower().strip()}|{type_}|{college_id or ''}|{page}|{page_size}"
        digest = hashlib.md5(raw.encode()).hexdigest()
        return f"{self.PREFIX}{digest}"

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get(
        self,
        q: str,
        type_: str,
        college_id: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int] | None:
        """
        Return (items, total) from cache, or None on miss / error.
        """
        if self._r is None:
            return None
        try:
            raw = await self._r.get(self._key(q, type_, college_id, page, page_size))
            if raw is None:
                return None
            payload = json.loads(raw)
            return payload["items"], payload["total"]
        except Exception as exc:
            logger.warning("Cache GET error (falling through to DB): %s", exc)
            return None

    # ── Write ─────────────────────────────────────────────────────────────────

    async def set(
        self,
        q: str,
        type_: str,
        college_id: str | None,
        page: int,
        page_size: int,
        items: list[dict[str, Any]],
        total: int,
        ttl: int,
    ) -> None:
        """Store (items, total) with an absolute TTL in seconds."""
        if self._r is None:
            return
        try:
            key = self._key(q, type_, college_id, page, page_size)
            value = json.dumps({"items": items, "total": total})
            await self._r.setex(key, ttl, value)
        except Exception as exc:
            logger.warning("Cache SET error: %s", exc)

    # ── Invalidate ────────────────────────────────────────────────────────────

    async def invalidate(self) -> int:
        """
        Delete every key under the "search:" namespace.

        Uses SCAN (non-blocking, cursor-based) instead of KEYS so we
        never block Redis on large keyspaces. Returns the count of
        deleted keys.

        Called after every full sync so stale data never lingers past
        the next re-index, regardless of the TTL.
        """
        if self._r is None:
            return 0
        try:
            deleted = 0
            async for key in self._r.scan_iter(match=f"{self.PREFIX}*", count=100):
                await self._r.delete(key)
                deleted += 1
            logger.info("Cache invalidated: %d keys deleted", deleted)
            return deleted
        except Exception as exc:
            logger.warning("Cache invalidate error: %s", exc)
            return 0
