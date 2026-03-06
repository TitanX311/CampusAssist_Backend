import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from post.models.post import Post


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
        """Fetch a post and lock the row (SELECT … FOR UPDATE).

        Use this before any mutation (add_comment, remove_comment, etc.) to prevent
        concurrent requests racing on the same row's array columns.
        """
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
        """Return all posts in a community (paginated)."""
        cid = uuid.UUID(community_id)
        condition = Post.community_id == cid

        total = (
            await self.db.execute(
                select(func.count()).select_from(Post).where(condition)
            )
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
        """Return all posts by a specific user inside a specific community (paginated)."""
        uid = uuid.UUID(user_id)
        cid = uuid.UUID(community_id)
        condition = (Post.user_id == uid) & (Post.community_id == cid)

        total = (
            await self.db.execute(
                select(func.count()).select_from(Post).where(condition)
            )
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

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Post], int]:
        """Return all posts (paginated), newest first. Admin use only."""
        total = (
            await self.db.execute(select(func.count()).select_from(Post))
        ).scalar_one()
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
        await self.db.delete(post)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Engagement helpers
    # ------------------------------------------------------------------

    async def increment_views(self, post: Post) -> Post:
        await self.db.execute(
            sql_update(Post)
            .where(Post.id == post.id)
            .values(views=Post.views + 1, updated_at=datetime.now(timezone.utc))
        )
        await self.db.refresh(post)
        return post

    async def add_like(self, post: Post) -> Post:
        await self.db.execute(
            sql_update(Post)
            .where(Post.id == post.id)
            .values(likes=Post.likes + 1, updated_at=datetime.now(timezone.utc))
        )
        await self.db.refresh(post)
        return post

    async def remove_like(self, post: Post) -> Post:
        await self.db.execute(
            sql_update(Post)
            .where(Post.id == post.id)
            .values(
                likes=func.greatest(Post.likes - 1, 0),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.refresh(post)
        return post

    async def add_comment(self, post: Post, comment_id: str) -> Post:
        """Append a comment UUID to the post's comments list."""
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
        """Remove a comment UUID from the post's comments list."""
        cid = uuid.UUID(comment_id)
        comments = list(post.comments)
        if cid in comments:
            comments.remove(cid)
            post.comments = comments
        post.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(post)
        return post
