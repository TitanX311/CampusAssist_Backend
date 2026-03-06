"""
gRPC servicer for community_service.

Handles:
  CheckMembership — verifies whether a user is a member of a community.

This servicer is started alongside the FastAPI/uvicorn server and listens on
a separate gRPC port (default 50052).  It reuses the same SQLAlchemy
async engine that the HTTP server uses.
"""
import uuid

import grpc
from sqlalchemy import select

from community.config.database import AsyncSessionLocal
from community.models.community import Community
from community.grpc.community_pb2 import CheckMembershipResponse
from community.grpc.community_pb2_grpc import CommunityServiceServicer


class CommunityServicer(CommunityServiceServicer):
    """Implements the CommunityService gRPC contract."""

    async def CheckMembership(self, request, context):
        community_id: str = request.community_id
        user_id: str = request.user_id

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Community).where(Community.id == community_id)
            )
            community = result.scalar_one_or_none()

        if community is None:
            return CheckMembershipResponse(
                exists=False,
                is_member=False,
                community_name="",
            )

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid user_id UUID")
            return CheckMembershipResponse()

        is_member = uid in (community.member_users or [])
        return CheckMembershipResponse(
            exists=True,
            is_member=is_member,
            community_name=community.name,
        )
