"""
Community membership checker for post_service — via gRPC.

Replaces the former httpx call to GET /api/community/{id}.
Calls community_service.CheckMembership over gRPC instead.
"""
import grpc
import grpc.aio

from fastapi import HTTPException, status

from post.config.settings import get_settings
from post.dependencies.auth import TokenPayload
from post.grpc import community_client


async def assert_community_member(
    community_id: str,
    current_user: TokenPayload,
) -> None:
    """
    Assert that `current_user` is an active member of `community_id`.

    Calls community_service via gRPC — no HTTP round-trip needed.

    Raises:
        HTTP 403 — user is not a member of the community.
        HTTP 404 — community does not exist.
        HTTP 502 — community_service gRPC call failed.
    """
    settings = get_settings()
    try:
        resp = await community_client.check_membership(
            target=settings.COMMUNITY_GRPC_TARGET,
            community_id=community_id,
            user_id=current_user.user_id,
        )
    except grpc.aio.AioRpcError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach community service: {exc.details()}",
        )

    if not resp.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    if not resp.is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this community.",
        )

    """
    Assert that `current_user` is an active member of `community_id`.

    Forwards the original ``Authorization`` header to community_service's
    ``GET /api/community/{community_id}`` endpoint and checks that the
    user's UUID appears in the returned ``member_users`` list.

    Args:
        community_id: UUID string of the target community.
        current_user: Decoded JWT payload from ``get_current_user``.
        request: The current FastAPI ``Request`` (used to forward the
                 Authorization header without re-encoding the token).

    Raises:
        HTTP 401 — token rejected by community_service.
        HTTP 403 — user is not a member of the community.
        HTTP 404 — community does not exist.
        HTTP 502 — community_service is unreachable or returned an error.
    """
    settings = get_settings()
    url = f"{settings.COMMUNITY_SERVICE_URL}/api/community/{community_id}"
    auth_header = request.headers.get("Authorization", "")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers={"Authorization": auth_header})
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach community service: {exc}",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from community service.",
        )

    data = response.json()
    member_uuids: list[str] = [str(uuid.UUID(m)) for m in data.get("member_users", [])]

    if str(uuid.UUID(current_user.user_id)) not in member_uuids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this community.",
        )
