"""
Community membership checker for comment_service — via gRPC.

Replaces the former httpx call to GET /api/community/{id}.
Calls community_service.CheckMembership over gRPC instead.
"""
import grpc
import grpc.aio

from fastapi import HTTPException, status

from comment.config.settings import get_settings
from comment.dependencies.auth import TokenPayload
from comment.grpc import clients as grpc_clients


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
        resp = await grpc_clients.check_membership(
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
