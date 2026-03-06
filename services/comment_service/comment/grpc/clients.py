"""
gRPC clients for comment_service.

community_client — calls community_service.CheckMembership
post_client      — calls post_service.AddComment / RemoveComment

Each client lazily creates one gRPC channel per target and reuses it.
Call close_all() during app shutdown.
"""
import logging

import grpc
import grpc.aio

from comment.grpc.community_pb2 import CheckMembershipRequest
from comment.grpc.community_pb2_grpc import CommunityServiceStub
from comment.grpc.post_pb2 import PostCommentRequest
from comment.grpc.post_pb2_grpc import PostServiceStub

logger = logging.getLogger(__name__)

_community_channel: grpc.aio.Channel | None = None
_community_stub: CommunityServiceStub | None = None

_post_channel: grpc.aio.Channel | None = None
_post_stub: PostServiceStub | None = None


# ---------------------------------------------------------------------------
# Community client
# ---------------------------------------------------------------------------

def _get_community_stub(target: str) -> CommunityServiceStub:
    global _community_channel, _community_stub
    if _community_stub is None:
        _community_channel = grpc.aio.insecure_channel(target)
        _community_stub = CommunityServiceStub(_community_channel)
    return _community_stub


async def check_membership(target: str, community_id: str, user_id: str):
    """
    Call community_service.CheckMembership via gRPC.

    Returns CheckMembershipResponse with .exists, .is_member, .community_name
    """
    stub = _get_community_stub(target)
    return await stub.CheckMembership(
        CheckMembershipRequest(community_id=community_id, user_id=user_id)
    )


# ---------------------------------------------------------------------------
# Post client
# ---------------------------------------------------------------------------

def _get_post_stub(target: str) -> PostServiceStub:
    global _post_channel, _post_stub
    if _post_stub is None:
        _post_channel = grpc.aio.insecure_channel(target)
        _post_stub = PostServiceStub(_post_channel)
    return _post_stub


async def add_comment(target: str, post_id: str, comment_id: str):
    """Call post_service.AddComment via gRPC."""
    stub = _get_post_stub(target)
    return await stub.AddComment(
        PostCommentRequest(post_id=post_id, comment_id=comment_id)
    )


async def remove_comment(target: str, post_id: str, comment_id: str):
    """Call post_service.RemoveComment via gRPC."""
    stub = _get_post_stub(target)
    return await stub.RemoveComment(
        PostCommentRequest(post_id=post_id, comment_id=comment_id)
    )


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

async def close_all() -> None:
    from comment.grpc import auth_client as _auth_client
    global _community_channel, _community_stub, _post_channel, _post_stub
    await _auth_client.close()
    if _community_channel is not None:
        await _community_channel.close()
        _community_channel = None
        _community_stub = None
    if _post_channel is not None:
        await _post_channel.close()
        _post_channel = None
        _post_stub = None
