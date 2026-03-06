"""
gRPC client for community_service — used by post_service.

Provides `check_membership(community_id, user_id)` which replaces the old
httpx call to GET /api/community/{id}.

A single gRPC channel is reused across requests (lazy-initialized).
Call `close()` during app shutdown to release the channel.
"""
import logging

import grpc
import grpc.aio

from post.grpc.community_pb2 import CheckMembershipRequest
from post.grpc.community_pb2_grpc import CommunityServiceStub

logger = logging.getLogger(__name__)

_channel: grpc.aio.Channel | None = None
_stub: CommunityServiceStub | None = None


def _get_stub(target: str) -> CommunityServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = grpc.aio.insecure_channel(target)
        _stub = CommunityServiceStub(_channel)
    return _stub


async def check_membership(target: str, community_id: str, user_id: str):
    """
    Call community_service.CheckMembership via gRPC.

    Args:
        target:       gRPC address, e.g. "community-service:50052"
        community_id: UUID string of the community.
        user_id:      UUID string of the user.

    Returns:
        CheckMembershipResponse with .exists, .is_member, .community_name
    """
    stub = _get_stub(target)
    request = CheckMembershipRequest(community_id=community_id, user_id=user_id)
    return await stub.CheckMembership(request)


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
