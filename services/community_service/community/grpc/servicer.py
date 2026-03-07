"""
gRPC servicer for community_service.

Handles:
  CheckMembership — verifies whether a user is a member of a community.

This servicer is started alongside the FastAPI/uvicorn server and listens on
a separate gRPC port (default 50052).  It reuses the same SQLAlchemy
async engine that the HTTP server uses.

ACID note: membership is now stored in the ``community_members`` join table
(not a denormalized UUID array), so the query here is a simple two-column
primary-key lookup — no deserialization of arrays needed.
"""
import uuid

import grpc
from sqlalchemy import select

from community.config.database import AsyncSessionLocal
from community.models.community import Community, CommunityMember
from community.grpc.community_pb2 import CheckMembershipResponse
from community.grpc.community_pb2_grpc import CommunityServiceServicer


class CommunityServicer(CommunityServiceServicer):
    """Implements the CommunityService gRPC contract."""

    async def CheckMembership(self, request, context):
        community_id: str = request.community_id
        user_id: str = request.user_id

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid user_id UUID")
            return CheckMembershipResponse()

        async with AsyncSessionLocal() as session:
            # Fetch community name (needed for the response)
            community_result = await session.execute(
                select(Community.name).where(Community.id == community_id)
            )
            community_name = community_result.scalar_one_or_none()

            if community_name is None:
                return CheckMembershipResponse(
                    exists=False,
                    is_member=False,
                    community_name="",
                )

            # Check membership via the join table — single indexed PK lookup
            member_result = await session.execute(
                select(CommunityMember).where(
                    CommunityMember.community_id == community_id,
                    CommunityMember.user_id == uid,
                )
            )
            is_member = member_result.scalar_one_or_none() is not None

        return CheckMembershipResponse(
            exists=True,
            is_member=is_member,
            community_name=community_name,
        )
