"""
Admin panel — aggregate stats from all services.
Returns total record counts in one parallel call.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import _auth_headers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])


class StatsResponse(BaseModel):
    users: int
    communities: int
    posts: int
    comments: int
    colleges: int
    attachments: int
    timestamp: str


async def _fetch_total(url: str, headers: dict) -> int:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers=headers, params={"page": 1, "page_size": 1})
            if r.status_code == 200:
                return r.json().get("total", 0)
    except Exception as exc:
        logger.warning("stats fetch failed for %s: %s", url, exc)
    return -1  # -1 signals an error for that resource


@router.get(
    "",
    response_model=StatsResponse,
    summary="[Admin] Aggregate stats",
    description=(
        "Returns total record counts for every resource across all services. "
        "A count of `-1` means that service was unreachable. "
        "Requires SUPER_ADMIN role."
    ),
)
async def get_stats(
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> StatsResponse:
    headers = _auth_headers(request)
    urls = {
        "users":       f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users",
        "communities": f"{settings.COMMUNITY_SERVICE_URL}/api/community/admin/list",
        "posts":       f"{settings.POST_SERVICE_URL}/api/posts/admin/list",
        "comments":    f"{settings.COMMENT_SERVICE_URL}/api/comments/admin/list",
        "colleges":    f"{settings.COLLEGE_SERVICE_URL}/api/college/admin/list",
        "attachments": f"{settings.ATTACHMENT_SERVICE_URL}/api/attachments/admin/list",
    }

    results = dict(
        zip(
            urls.keys(),
            await asyncio.gather(*[_fetch_total(u, headers) for u in urls.values()]),
        )
    )

    return StatsResponse(
        users=results["users"],
        communities=results["communities"],
        posts=results["posts"],
        comments=results["comments"],
        colleges=results["colleges"],
        attachments=results["attachments"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
