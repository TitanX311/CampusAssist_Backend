"""
HTTP clients for fetching stats from post, comment, and community services.

Each service exposes an internal endpoint (not reachable via ingress) that
returns aggregate counts for a given user_id.  We call all three in parallel
with asyncio.gather so the total latency is bounded by the slowest service.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def _safe_get(url: str) -> dict:
    """GET *url* and return the parsed JSON, or {} on any error."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Stats fetch failed for %s: %s", url, exc)
    return {}


async def fetch_user_stats(
    post_service_url: str,
    comment_service_url: str,
    community_service_url: str,
    user_id: str,
) -> dict[str, int]:
    """
    Fetch post_count, comment_count, and community_count for *user_id* in
    parallel.  Falls back to 0 for any service that is unreachable.
    """
    post_url = f"{post_service_url}/internal/stats/users/{user_id}"
    comment_url = f"{comment_service_url}/internal/stats/users/{user_id}"
    community_url = f"{community_service_url}/internal/stats/users/{user_id}"

    post_data, comment_data, community_data = await asyncio.gather(
        _safe_get(post_url),
        _safe_get(comment_url),
        _safe_get(community_url),
    )

    return {
        "post_count": int(post_data.get("count", 0)),
        "comment_count": int(comment_data.get("count", 0)),
        "community_count": int(community_data.get("count", 0)),
    }
