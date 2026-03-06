"""gRPC servicer for auth_service — GetUser RPC."""
import grpc

from auth.config.database import AsyncSessionLocal
from auth.models.user import User
from auth.grpc.auth_pb2 import GetUserResponse
from auth.grpc.auth_pb2_grpc import AuthServiceServicer
from sqlalchemy import select


class AuthServicer(AuthServiceServicer):
    async def GetUser(self, request, context):
        user_id: str = request.user_id
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user: User | None = result.scalar_one_or_none()

        if user is None:
            return GetUserResponse(found=False)

        return GetUserResponse(
            found=True,
            id=str(user.id),
            email=user.email,
            name=user.name or "",
            picture=user.picture or "",
            type=user.type.value,
            is_active=user.is_active,
        )
