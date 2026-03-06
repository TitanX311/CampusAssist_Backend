"""
gRPC servicer for post_service.

Handles:
  AddComment    — appends a comment UUID to a post's comments array.
  RemoveComment — removes a comment UUID from a post's comments array.

Listens on a separate gRPC port (default 50053).
"""
import grpc
from sqlalchemy.ext.asyncio import AsyncSession

from post.config.database import AsyncSessionLocal
from post.repositories.post_repository import PostRepository
from post.grpc.post_pb2 import PostCommentResponse
from post.grpc.post_pb2_grpc import PostServiceServicer


class PostServicer(PostServiceServicer):
    """Implements the PostService gRPC contract."""

    async def AddComment(self, request, context):
        post_id: str = request.post_id
        comment_id: str = request.comment_id

        async with AsyncSessionLocal() as session:
            repo = PostRepository(session)
            post = await repo.get_by_id(post_id)
            if post is None:
                return PostCommentResponse(success=False, message="Post not found")
            await repo.add_comment(post, comment_id)
            await session.commit()

        return PostCommentResponse(success=True, message="")

    async def RemoveComment(self, request, context):
        post_id: str = request.post_id
        comment_id: str = request.comment_id

        async with AsyncSessionLocal() as session:
            repo = PostRepository(session)
            post = await repo.get_by_id(post_id)
            if post is None:
                return PostCommentResponse(success=False, message="Post not found")
            await repo.remove_comment(post, comment_id)
            await session.commit()

        return PostCommentResponse(success=True, message="")
