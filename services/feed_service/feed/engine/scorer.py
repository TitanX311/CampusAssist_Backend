"""
Feed scoring engine.

Two feeds are supported:

MY FEED  (personalised, two-tier)
  The ranked list is split into two sections that are concatenated:

  Section 1 — RECENT  (age ≤ FEED_RECENT_WINDOW_HOURS, default 24 h)
    Posts are sorted newest-first so users always see what's happening now.
    score = 1000 + (1 − age / recent_hours) × 100     → range 1000–1100

  Section 2 — POPULAR  (older posts)
    Posts are sorted by engagement so the best content from the last week
    surfaces even after it leaves the "recent" window.
    score = likes × 3 + comment_count × 2 + views × 0.05   → range 0–…

  Because Section 1 scores are ≥ 1000 and Section 2 scores are < 1000
  (for any realistic engagement count) the two tiers are naturally
  separated when sorted descending by score.

ACROSS-INDIA FEED  (shared discovery, pure-engagement recommendation)
  Only posts that have REAL engagement (score ≥ INDIA_FEED_MIN_ENGAGEMENT)
  are included — zero-engagement posts are filtered out so this surface
  always shows content the community has already validated.

  score = likes × 5 + comment_count × 3 + views × 0.1

  No recency component — a week-old post with 20 likes beats a brand-new
  post with 0 likes on this surface.  The my-feed already handles recency.

  Cache is shared — one Redis key for all users, TTL 10 min.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from feed.config.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ── Fetching helpers — MY FEED ──────────────────────────────────────────────
# ---------------------------------------------------------------------------

async def _fetch_community_ids(user_id: str) -> list[str]:
    """Return the community IDs the user is a member of."""
    settings = get_settings()
    url = f"{settings.COMMUNITY_SERVICE_URL}/internal/feed/communities/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json().get("community_ids", [])
    except Exception as exc:
        logger.warning("Failed to fetch communities for %s: %s", user_id, exc)
        return []


async def _fetch_posts_for_community(
    community_id: str,
    since_hours: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Return recent posts from a single community via post_service internal route."""
    settings = get_settings()
    url = f"{settings.POST_SERVICE_URL}/internal/feed/posts"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                url,
                params={
                    "community_id": community_id,
                    "since_hours": since_hours,
                    "limit": limit,
                },
            )
            resp.raise_for_status()
            return resp.json().get("posts", [])
    except Exception as exc:
        logger.warning("Failed to fetch posts for community %s: %s", community_id, exc)
        return []


# ---------------------------------------------------------------------------
# ── Fetching helpers — INDIA FEED ───────────────────────────────────────────
# ---------------------------------------------------------------------------

async def _fetch_public_community_ids() -> list[str]:
    """Return all PUBLIC community IDs across every college."""
    settings = get_settings()
    url = f"{settings.COMMUNITY_SERVICE_URL}/internal/feed/public-community-ids"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json().get("community_ids", [])
    except Exception as exc:
        logger.warning("Failed to fetch public community IDs: %s", exc)
        return []


async def _fetch_trending_posts(
    community_ids: list[str],
    since_hours: int,
    limit: int,
    min_engagement: int = 0,
) -> list[dict[str, Any]]:
    """Fetch the most-engaged posts from a set of communities in one HTTP call.

    post_service orders rows by engagement score (likes×5 + comments×3 +
    views×0.1) at the DB level, so we receive them pre-sorted.
    Only posts whose engagement score ≥ *min_engagement* are returned.
    """
    settings = get_settings()
    url = f"{settings.POST_SERVICE_URL}/internal/feed/trending-posts"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                json={
                    "community_ids": community_ids,
                    "since_hours": since_hours,
                    "limit": limit,
                    "min_engagement": min_engagement,
                },
            )
            resp.raise_for_status()
            return resp.json().get("posts", [])
    except Exception as exc:
        logger.warning("Failed to fetch trending posts: %s", exc)
        return []


# ---------------------------------------------------------------------------
# ── Scoring ──────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _age_hours(post: dict[str, Any]) -> float:
    try:
        created_at = datetime.fromisoformat(post["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created_at).total_seconds() / 3600.0
    except Exception:
        return 999.0


def _score_recent(post: dict[str, Any], recent_hours: int) -> float:
    """Score for Section 1 (recent posts ≤ recent_hours old).

    Range: 1000–1100.  Newest post gets ~1100; a post exactly at the
    boundary gets exactly 1000.

    score = 1000 + (1 − age / recent_hours) × 100
    """
    age = _age_hours(post)
    return round(1000.0 + max(0.0, 1.0 - age / recent_hours) * 100.0, 4)


def _score_popular(post: dict[str, Any]) -> float:
    """Score for Section 2 (older posts ranked by engagement).

    score = likes × 3 + comment_count × 2 + views × 0.05
    """
    return round(
        post.get("likes", 0) * 3.0
        + post.get("comment_count", 0) * 2.0
        + post.get("views", 0) * 0.05,
        4,
    )


def _score_india_post(post: dict[str, Any]) -> float:
    """Pure-engagement score for the Across-India recommendation feed.

    No recency component — this surface surfaces the BEST content regardless
    of age.  Recency is already handled by My Feed.

    score = likes × 5 + comment_count × 3 + views × 0.1
    """
    return round(
        post.get("likes", 0) * 5.0
        + post.get("comment_count", 0) * 3.0
        + post.get("views", 0) * 0.1,
        4,
    )


# ---------------------------------------------------------------------------
# ── My Feed builder ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

async def build_feed(user_id: str) -> list[dict[str, Any]]:
    """Build a personalised two-tier feed for *user_id*.

    Tier 1 — RECENT (age ≤ FEED_RECENT_WINDOW_HOURS)
        Sorted newest-first.  Users always see what is happening *right now*
        in their communities before anything else.

    Tier 2 — POPULAR (older posts)
        Sorted by engagement (likes×3 + comments×2 + views×0.05) so the best
        content from the past week bubbles up after users have caught up on
        today's posts.

    The two tiers are concatenated; scores are chosen so Tier 1 ≥ 1000 and
    Tier 2 < 1000 (unless a post has >333 likes, which is fine — it will
    still appear after all recent posts).

    Returns an empty list if the user is not in any community.
    """
    settings = get_settings()
    community_ids = await _fetch_community_ids(user_id)
    if not community_ids:
        return []

    sem = asyncio.Semaphore(20)

    async def _bounded_fetch(cid: str) -> list[dict[str, Any]]:
        async with sem:
            return await _fetch_posts_for_community(
                cid,
                since_hours=settings.FEED_WINDOW_HOURS,
                limit=settings.FEED_POSTS_PER_COMMUNITY,
            )

    results = await asyncio.gather(*[_bounded_fetch(cid) for cid in community_ids])

    # Deduplicate
    seen_ids: set[str] = set()
    posts: list[dict[str, Any]] = []
    for batch in results:
        for p in batch:
            pid = p.get("post_id") or p.get("id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                posts.append(p)

    recent_hours = settings.FEED_RECENT_WINDOW_HOURS

    recent: list[dict[str, Any]] = []
    popular: list[dict[str, Any]] = []

    for p in posts:
        age = _age_hours(p)
        if age <= recent_hours:
            p["score"] = _score_recent(p, recent_hours)
            recent.append(p)
        else:
            p["score"] = _score_popular(p)
            popular.append(p)

    # Section 1: newest first (highest score = most recent)
    recent.sort(key=lambda p: p["score"], reverse=True)
    # Section 2: most-engaged first
    popular.sort(key=lambda p: p["score"], reverse=True)

    return recent + popular


# ---------------------------------------------------------------------------
# ── Across-India Feed builder ────────────────────────────────────────────────
# ---------------------------------------------------------------------------

async def build_india_feed() -> list[dict[str, Any]]:
    """Build the shared Across-India recommendation feed.

    Only posts that have REAL engagement (score ≥ INDIA_FEED_MIN_ENGAGEMENT)
    are included.  This turns the feed into a genuine recommendation surface —
    posts need at least one like or comment to appear here.

    Scoring is pure engagement with no recency factor so that the best content
    from the past week is always surfaced, regardless of age.

    The result is stored under a single shared Redis key (not per-user) and
    cached for INDIA_FEED_CACHE_TTL_SECONDS (default 10 min).
    """
    settings = get_settings()
    community_ids = await _fetch_public_community_ids()
    if not community_ids:
        return []

    posts = await _fetch_trending_posts(
        community_ids=community_ids,
        since_hours=settings.INDIA_FEED_WINDOW_HOURS,
        limit=settings.INDIA_FEED_TOP_N,
        min_engagement=settings.INDIA_FEED_MIN_ENGAGEMENT,
    )

    # Deduplicate (safety net)
    seen_ids: set[str] = set()
    unique: list[dict[str, Any]] = []
    for p in posts:
        pid = p.get("post_id") or p.get("id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique.append(p)

    # Score — pure engagement, no recency
    for p in unique:
        p["score"] = _score_india_post(p)

    # Filter out posts with zero engagement score (extra safety net — post_service
    # already filters by min_engagement but we double-check here)
    unique = [p for p in unique if p["score"] > 0]

    unique.sort(key=lambda p: p["score"], reverse=True)
    return unique
