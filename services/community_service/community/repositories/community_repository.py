import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from community.models.community import Community, CommunityType


class CommunityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, community_id: str) -> Community | None:
        result = await self.db.execute(
            select(Community).where(Community.id == community_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, community_id: str) -> Community | None:
        """Fetch a community and lock the row (SELECT … FOR UPDATE).

        Use this before any mutation (add_member, remove_member, etc.) to prevent
        concurrent requests from racing on the same row's array columns.
        """
        result = await self.db.execute(
            select(Community).where(Community.id == community_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Community | None:
        result = await self.db.execute(
            select(Community).where(Community.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_member(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Community], int]:
        """Return all communities the given user is a member of (paginated).

        Uses Postgres's native @> (array contains) operator:
            member_users @> ARRAY[<uuid>]
        which is a single indexed scan — no cross-service call needed.
        """
        uid = uuid.UUID(user_id)
        condition = Community.member_users.contains([uid])

        count_query = select(func.count()).select_from(Community).where(condition)
        total = (await self.db.execute(count_query)).scalar_one()

        items = (
            await self.db.execute(
                select(Community)
                .where(condition)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    async def get_by_college(
        self,
        college_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Community], int]:
        """Return all communities belonging to a given college (paginated).

        Uses Postgres's native @> (array contains) operator:
            parent_colleges @> ARRAY[<uuid>]
        """
        uid = uuid.UUID(college_id)
        condition = Community.parent_colleges.contains([uid])

        count_query = select(func.count()).select_from(Community).where(condition)
        total = (await self.db.execute(count_query)).scalar_one()

        items = (
            await self.db.execute(
                select(Community)
                .where(condition)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        type_filter: CommunityType | None = None,
    ) -> tuple[list[Community], int]:
        """Return a paginated list of communities and the total count."""
        query = select(Community)
        count_query = select(func.count()).select_from(Community)

        if type_filter is not None:
            query = query.where(Community.type == type_filter)
            count_query = count_query.where(Community.type == type_filter)

        total = (await self.db.execute(count_query)).scalar_one()
        items = (
            await self.db.execute(
                query.offset((page - 1) * page_size).limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    # ------------------------------------------------------------------
    # Create / update / delete
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        type: CommunityType,
        creator_user_id: str,
        parent_colleges: list[uuid.UUID] | None = None,
    ) -> Community:
        """Create a new community. The creator is automatically added as a member."""
        community = Community(
            name=name,
            type=type,
            member_users=[uuid.UUID(creator_user_id)],
            parent_colleges=parent_colleges or [],
        )
        self.db.add(community)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def update(
        self,
        community: Community,
        name: str | None = None,
        type: CommunityType | None = None,
    ) -> Community:
        if name is not None:
            community.name = name
        if type is not None:
            community.type = type
        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def delete(self, community: Community) -> None:
        await self.db.delete(community)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    async def add_member(self, community: Community, user_id: str) -> Community:
        """Move a user from requested_users (if present) into member_users."""
        uid = uuid.UUID(user_id)
        members = list(community.member_users)
        if uid not in members:
            members.append(uid)
            community.member_users = members

        requested = list(community.requested_users)
        if uid in requested:
            requested.remove(uid)
            community.requested_users = requested

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def remove_member(self, community: Community, user_id: str) -> Community:
        """Remove a user from member_users."""
        uid = uuid.UUID(user_id)
        members = list(community.member_users)
        if uid in members:
            members.remove(uid)
            community.member_users = members

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def request_join(self, community: Community, user_id: str) -> Community:
        """Add a user to requested_users (for PRIVATE communities)."""
        uid = uuid.UUID(user_id)
        requested = list(community.requested_users)
        if uid not in requested:
            requested.append(uid)
            community.requested_users = requested

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def reject_request(self, community: Community, user_id: str) -> Community:
        """Remove a user from requested_users without adding to members."""
        uid = uuid.UUID(user_id)
        requested = list(community.requested_users)
        if uid in requested:
            requested.remove(uid)
            community.requested_users = requested

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    async def add_post(self, community: Community, post_id: str) -> Community:
        """Append a post UUID to the community's post list."""
        pid = uuid.UUID(post_id)
        posts = list(community.posts)
        if pid not in posts:
            posts.append(pid)
            community.posts = posts

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def remove_post(self, community: Community, post_id: str) -> Community:
        """Remove a post UUID from the community's post list."""
        pid = uuid.UUID(post_id)
        posts = list(community.posts)
        if pid in posts:
            posts.remove(pid)
            community.posts = posts

        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community
