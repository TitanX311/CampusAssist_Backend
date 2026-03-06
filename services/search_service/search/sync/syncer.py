"""
Data syncer — fetches all colleges and communities from upstream services
and upserts them into the local search index.

Uses a short-lived service token minted from the shared SECRET_KEY so it
can call college/community endpoints that require authentication.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from jose import jwt

logger = logging.getLogger(__name__)


def _mint_service_token(secret_key: str, algorithm: str = "HS256") -> str:
    """Mint a 10-minute service-to-service access token."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "search-service",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        secret_key,
        algorithm=algorithm,
    )


async def _paginate(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """Exhaust all pages of a paginated endpoint and return flat list."""
    items: list[dict] = []
    page = 1
    while True:
        resp = await client.get(url, headers=headers, params={"page": page, "page_size": page_size})
        resp.raise_for_status()
        batch = resp.json().get("items", [])
        items.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return items


async def sync_all(settings: Any, session_factory: Any) -> dict[str, Any]:
    """
    Full re-index: fetch every college and every community, upsert all.

    Returns a dict with counts and any per-item errors.
    """
    from search.repositories.search_repository import SearchRepository

    token = _mint_service_token(settings.SECRET_KEY, settings.ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}
    stats: dict[str, Any] = {"colleges": 0, "communities": 0, "errors": []}

    t0 = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # ── 1. Colleges ─────────────────────────────────────────────────
            try:
                colleges = await _paginate(
                    client,
                    f"{settings.COLLEGE_SERVICE_URL}/api/college",
                    headers,
                )
            except Exception as exc:
                logger.error("Failed to fetch colleges: %s", exc)
                stats["errors"].append(f"colleges: {exc}")
                colleges = []

            async with session_factory() as session:
                repo = SearchRepository(session)
                for college in colleges:
                    try:
                        await repo.upsert_college(college)
                    except Exception as exc:
                        logger.error("Failed to upsert college %s: %s", college.get("id"), exc)
                        stats["errors"].append(f"college {college.get('id')}: {exc}")
                await session.commit()
            stats["colleges"] = len(colleges)
            logger.info("Indexed %d colleges", len(colleges))

            # ── 2. Communities (via each college) ───────────────────────────
            for college in colleges:
                cid = college["id"]
                try:
                    communities = await _paginate(
                        client,
                        f"{settings.COMMUNITY_SERVICE_URL}/api/community/college/{cid}",
                        headers,
                    )
                except Exception as exc:
                    logger.error("Failed to fetch communities for college %s: %s", cid, exc)
                    stats["errors"].append(f"communities for {cid}: {exc}")
                    continue

                async with session_factory() as session:
                    repo = SearchRepository(session)
                    for community in communities:
                        try:
                            await repo.upsert_community(community)
                        except Exception as exc:
                            logger.error(
                                "Failed to upsert community %s: %s",
                                community.get("id"), exc,
                            )
                            stats["errors"].append(f"community {community.get('id')}: {exc}")
                    await session.commit()
                stats["communities"] += len(communities)

            logger.info("Indexed %d communities", stats["communities"])

    except Exception as exc:
        logger.error("Sync failed: %s", exc)
        stats["errors"].append(f"fatal: {exc}")

    # ── Invalidate the Redis search cache ────────────────────────────────────
    # Always flush after a sync (even partial) so stale entries are evicted
    # immediately rather than waiting for TTL expiry.
    try:
        from search.cache.backend import get_cache
        deleted = await get_cache().invalidate()
        logger.info("Cache invalidated after sync: %d keys deleted", deleted)
    except Exception as exc:
        logger.warning("Cache invalidation after sync failed: %s", exc)

    stats["duration_seconds"] = round(time.monotonic() - t0, 2)
    return stats


async def background_sync_loop(settings: Any, session_factory: Any) -> None:
    """
    Long-running background task that re-syncs every SYNC_INTERVAL_SECONDS.
    Runs until the process exits.
    """
    interval = settings.SYNC_INTERVAL_SECONDS
    if interval <= 0:
        logger.info("Background sync disabled (SYNC_INTERVAL_SECONDS=%d)", interval)
        return

    logger.info(
        "Background sync enabled — first run in %ds, then every %ds", interval, interval
    )
    await asyncio.sleep(interval)  # give services time to start

    while True:
        logger.info("Background sync starting …")
        try:
            stats = await sync_all(settings, session_factory)
            logger.info(
                "Background sync done: %d colleges, %d communities, %d errors, %.1fs",
                stats["colleges"],
                stats["communities"],
                len(stats["errors"]),
                stats["duration_seconds"],
            )
        except Exception as exc:
            logger.error("Background sync loop error: %s", exc)
        await asyncio.sleep(interval)
