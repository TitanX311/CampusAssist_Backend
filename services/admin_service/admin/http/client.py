"""
Shared httpx helpers for proxying requests to internal services.

The admin_service forwards the caller's Authorization header so backend
service admin routes can perform their own SUPER_ADMIN gRPC checks.
"""
from __future__ import annotations

import httpx
from fastapi import Request


def _auth_headers(request: Request) -> dict[str, str]:
    """Extract the Authorization header from the incoming request."""
    auth = request.headers.get("Authorization", "")
    return {"Authorization": auth} if auth else {}


async def api_get(
    url: str,
    request: Request,
    params: dict | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.get(url, headers=_auth_headers(request), params=params)


async def api_delete(url: str, request: Request) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.delete(url, headers=_auth_headers(request))


async def api_patch(
    url: str,
    request: Request,
    body: dict,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.patch(url, headers=_auth_headers(request), json=body)


def raise_for_upstream(resp: httpx.Response) -> None:
    """Raise HTTPException propagating the upstream status code + detail."""
    if resp.status_code >= 400:
        from fastapi import HTTPException
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)
