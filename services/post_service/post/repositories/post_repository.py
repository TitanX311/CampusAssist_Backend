"""Post repository.

ACID guarantees
---------------
* ``get_by_id_for_update`` locks the row before mutations (array columns,
  counter updates) to prevent lost-update races.
* Like / unlike use ``INSERT … ON CONFLICT DO NOTHING RETURNING`` so a double-
  like is detected at the DB level without a separate SELECT.  The ``likes``
  counter is only bumped/decremented when a row was actually inserted/deleted.
* ``func.greatest(likes - 1, 0)`` prevents the counter from going negative.
* All mutations flush inside the open session; commit/rollback is handled by
  the ``get_db`` FastAPI dependency.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update as sql_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from post.models.post import Post, PostLike


class PostRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, post_id: str) -> Post | None:
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, post_id: str) -> Post | None:
        """Fetch a post and lock the row (SELECT … FOR UPDATE)."""
        result = await self.db.execute(
            select(Post).where(Post.id == post_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_community(
        self,
        community_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Post], int]:
        cid = uuid.UUID(community_id)
        condition = Post.community_id == cid
        total = (
            await self.db.execute(select(func.count()).select_from(Post).where(condition))
        ).scalar_one()
        items = (
            await self.db.execute(
                select(Post)
                .where(condition)
                .order_by(Post.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    async def get_by_user_in_community(
        self,
        user_id: str,
        community_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Post], int]:
        uid = uuid.UUID(user_id)
        cid = uuid.UUID(community_id)
        condition = (Post.user_id == uid) & (Post.community_id == cid)
        total = (
            await self.db.execute(select(func.count()).select_from(Post).where(condition))
        ).scalar_one()
        items = (
            await self.db.execute(
                select(Post)
                .where(condition)
                .order_by(Post.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    async def get_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Post], int]:
        total = (await self.db.execute(select(func.count()).select_from(Post))).scalar_one()
        items = (
            await self.db.execute(
                select(Post)
                .order_by(Post.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    # ------------------------------------------------------------------
    # Like status helpers
    # ------------------------------------------------------------------

    async def is_liked_by(self, post_id: str, user_id: str) -> bool:
        """Check whether the given user has liked the given post."""
        uid = uuid.UUID(user_id)
        row = (
            await self.db.execute(
                select(PostLike).where(
                    PostLike.post_id == post_id,
                    PostLike.user_id == uid,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def get_viewer_like_map(
        self, post_ids: list[str], user_id: str
    ) -> dict[str, bool]:
        """Return {post_id: liked_by_me} for the viewer.

        Single indexed query regardless of list size — O(1) round trips.
        """
        if not post_ids:
            return {}
        uid = uuid.UUID(user_id)
        liked_ids = set(
            (
                await self.db.execute(
                    select(PostLike.post_id).where(
                        PostLike.post_id.in_(post_ids),
                        PostLike.user_id == uid,
                    )
                )
            ).scalars().all()
        )
        return {pid: pid in liked_ids for pid in post_ids}

    # ------------------------------------------------------------------
    # Create / update / delete
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: str,
        community_id: str,
        content: str,
        attachments: list[uuid.UUID] | None = None,
    ) -> Post:
        post = Post(
            user_id=uuid.UUID(user_id),
            community_id=uuid.UUID(community_id),
            content=content,
            attachments=attachments or [],
        )
        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def update(
        self,
        post: Post,
        content: str | None = None,
        attachments: list[uuid.UUID] | None = None,
    ) -> Post:
        if content is not None:
            post.content = content
        if attachments is not None:
            post.attachments = attachments
        post.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        # ON DELETE CASCADE removes PostLike rows automatically.
        await self.db.delete(post)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Engagement — views
    # ------------------------------------------------------------------

    async def increment_views(self, post: Post) -> Post:
        await self.db.execute(
            sql_update(Post)
            .where(Post.id == post.id)
            .values(views=Post.views + 1, updated_at=datetime.now(timezone.utc))
        )
        await self.db.refresh(post)
        return post

    # ------------------------------------------------------------------
    # Engagement — likes (join table + counter)
    # ------------------------------------------------------------------

    async def like(self, post: Post, user_id: str) -> tuple[Post, bool]:
        """Toggle like ON.

        Returns (post, liked) where liked=True means the like was newly added,
        False means the user had already liked this post (idempotent).

        ACID: INSERT ON CONFLICT DO NOTHING RETURNING ensures only one
        winner in a race — the counter is bumped only when the row inserts.
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            pg_insert(PostLike)
            .values(post_id=post.id, user_id=uid, liked_at=datetime.now(timezone.utc))
            .on_conflict_do_nothing()
            .returning(PostLike.post_id)
        )
        inserted = result.scalar_one_or_none() is not None
        if inserted:
            await self.db.execute(
                sql_update(Post)
                .where(Post.id == post.id)
                .values(likes=Post.likes + 1, updated_at=datetime.now(timezone.utc))
            )
        await self.db.refresh(post)
        return post, inserted

    async def unlike(self, post: Post, user_id: str) -> tuple[Post, bool]:
        """Toggle like OFF.

        Returns (post, unliked) where unliked=True means the like was removed,
        False means the user had not liked this post (idempotent).
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            delete(PostLike)
            .where(PostLike.post_id == post.id, PostLike.user_id == uid)
            .returning(PostLike.post_id)
        )
        deleted = result.scalar_one_or_none() is not None
        if deleted:
            await self.db.execute(
                sql_update(Post)
                .where(Post.id == post.id)
                .values(
                    likes=func.greatest(Post.likes - 1, 0),
                    updated_at=datetime.now(timezone.utc),
                )
            )
        await self.db.refresh(post)
        return post, deleted

    # ------------------------------------------------------------------
    # Comments (cross-service UUID array)
    # ------------------------------------------------------------------

    async def add_comment(self, post: Post, comment_id: str) -> Post:
        cid = uuid.UUID(comment_id)
        comments = list(post.comments)
        if cid not in comments:
            comments.append(cid)
            post.comments = comments
        post.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def remove_comment(self, post: Post, comment_id: str) -> Post:
        cid = uuid.UUID(comment_id)
        comments = list(post.comments)
        if cid in comments:
            comments.remove(cid)
            post.comments = comments
        post.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(post)
        return post


