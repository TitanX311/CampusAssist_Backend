import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy import update as sql_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from comment.models.comment import Comment, CommentLike


class CommentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, comment_id: str) -> Comment | None:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, comment_id: str) -> Comment | None:
        """Fetch a comment and lock the row (SELECT … FOR UPDATE).

        Use this before any mutating update or delete to prevent concurrent
        requests from racing on the same row.
        """
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id).with_for_update()
        )
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

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Comment], int]:
        """Return all comments (paginated), newest first. Admin use only."""
        total = (
            await self.db.execute(select(func.count()).select_from(Comment))
        ).scalar_one()
        items = (
            await self.db.execute(
                select(Comment)
                .order_by(Comment.created_at.desc())
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

    async def like(self, comment: Comment, user_id: str) -> tuple[Comment, bool]:
        """Add a like from *user_id* to *comment*.

        Uses ``INSERT … ON CONFLICT DO NOTHING RETURNING`` so the operation is
        idempotent and race-safe — no row lock on the parent is needed.  The
        ``likes`` counter is only incremented when an actual insert occurs.

        Returns ``(updated_comment, True)`` when the like was newly added, or
        ``(comment, False)`` when it was already present.
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            pg_insert(CommentLike)
            .values(comment_id=comment.id, user_id=uid, liked_at=datetime.now(timezone.utc))
            .on_conflict_do_nothing()
            .returning(CommentLike.comment_id)
        )
        inserted = result.scalar_one_or_none() is not None
        if inserted:
            await self.db.execute(
                sql_update(Comment)
                .where(Comment.id == comment.id)
                .values(likes=Comment.likes + 1, updated_at=datetime.now(timezone.utc))
            )
            await self.db.refresh(comment)
        return comment, inserted

    async def unlike(self, comment: Comment, user_id: str) -> tuple[Comment, bool]:
        """Remove a like from *user_id* on *comment*.

        Only decrements the counter when a row was actually deleted, and uses
        ``func.greatest(likes - 1, 0)`` to guard against going negative.

        Returns ``(updated_comment, True)`` when the like was removed, or
        ``(comment, False)`` when no like existed.
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            delete(CommentLike)
            .where(CommentLike.comment_id == comment.id, CommentLike.user_id == uid)
            .returning(CommentLike.comment_id)
        )
        deleted = result.scalar_one_or_none() is not None
        if deleted:
            await self.db.execute(
                sql_update(Comment)
                .where(Comment.id == comment.id)
                .values(
                    likes=func.greatest(Comment.likes - 1, 0),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await self.db.refresh(comment)
        return comment, deleted

    async def is_liked_by(self, comment_id: str, user_id: str) -> bool:
        """Return ``True`` if *user_id* has liked *comment_id*."""
        uid = uuid.UUID(user_id)
        row = (
            await self.db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == uid,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def get_viewer_like_map(
        self, comment_ids: list[str], user_id: str
    ) -> dict[str, bool]:
        """Return a mapping of comment_id → liked_by_viewer for a batch of IDs.

        Issues a single ``SELECT … WHERE comment_id IN (…) AND user_id = ?``
        query regardless of page size — no N+1 round-trips.
        """
        if not comment_ids:
            return {}
        uid = uuid.UUID(user_id)
        liked_ids = set(
            (
                await self.db.execute(
                    select(CommentLike.comment_id).where(
                        CommentLike.comment_id.in_(comment_ids),
                        CommentLike.user_id == uid,
                    )
                )
            )
            .scalars()
            .all()
        )
        return {cid: cid in liked_ids for cid in comment_ids}

    async def get_reply_count(self, comment_id: str) -> int:
        """Return the number of direct replies to *comment_id*."""
        result = await self.db.execute(
            select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id)
        )
        return result.scalar_one() or 0
