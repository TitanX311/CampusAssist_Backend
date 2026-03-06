import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from comment.models.comment import Comment


class CommentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, comment_id: str) -> Comment | None:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        return result.scalar_one_or_none()

    async def get_by_post(
        self,
        post_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Comment], int]:
        """Return top-level comments for a post (parent_id IS NULL), newest first."""
        pid = uuid.UUID(post_id)
        condition = (Comment.post_id == pid) & (Comment.parent_id.is_(None))

        total = (
            await self.db.execute(
                select(func.count()).select_from(Comment).where(condition)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Comment)
                .where(condition)
                .order_by(Comment.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    async def get_replies(
        self,
        parent_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Comment], int]:
        """Return direct replies to a comment (parent_id = parent_id), oldest first."""
        condition = Comment.parent_id == parent_id

        total = (
            await self.db.execute(
                select(func.count()).select_from(Comment).where(condition)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Comment)
                .where(condition)
                .order_by(Comment.created_at.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    # ------------------------------------------------------------------
    # Create / update / delete
    # ------------------------------------------------------------------

    async def create(
        self,
        post_id: str,
        user_id: str,
        community_id: str,
        content: str,
    ) -> Comment:
        comment = Comment(
            post_id=uuid.UUID(post_id),
            user_id=uuid.UUID(user_id),
            community_id=uuid.UUID(community_id),
            content=content,
        )
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def update(
        self,
        comment: Comment,
        content: str | None = None,
    ) -> Comment:
        if content is not None:
            comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def delete(self, comment: Comment) -> None:
        await self.db.delete(comment)
        await self.db.flush()

    async def create_reply(
        self,
        parent: Comment,
        user_id: str,
        content: str,
    ) -> Comment:
        """
        Create a reply to ``parent``.

        The reply inherits ``post_id`` and ``community_id`` from the parent and
        stores a ``parent_id`` back-reference so the full thread can be traversed
        in either direction with simple ``WHERE parent_id = ?`` queries.
        """
        reply = Comment(
            post_id=parent.post_id,
            user_id=uuid.UUID(user_id),
            community_id=parent.community_id,
            parent_id=parent.id,
            content=content,
        )
        self.db.add(reply)
        await self.db.flush()
        await self.db.refresh(reply)
        return reply

    # ------------------------------------------------------------------
    # Engagement helpers
    # ------------------------------------------------------------------

    async def toggle_like(self, comment: Comment, user_id: str) -> tuple[Comment, bool]:
        """
        Toggle a like for ``user_id`` on ``comment``.

        Returns ``(updated_comment, liked)`` where ``liked`` is ``True`` if the
        like was added and ``False`` if it was removed.
        """
        uid = uuid.UUID(user_id)
        liked_by = list(comment.liked_by)
        if uid in liked_by:
            liked_by.remove(uid)
            liked = False
        else:
            liked_by.append(uid)
            liked = True

        comment.liked_by = liked_by
        comment.likes = len(liked_by)
        comment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment, liked
