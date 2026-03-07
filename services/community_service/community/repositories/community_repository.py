"""Community repository.

All write paths that touch membership maintain two invariants atomically
inside a single SQLAlchemy session (and therefore a single DB transaction):

1. The ``CommunityMember`` / ``CommunityJoinRequest`` join tables hold the
   canonical, row-level-lockable source of truth.
2. The denormalized ``Community.member_count`` counter stays in sync via
   ``UPDATE … SET member_count = member_count ± 1`` — no full array scan needed.

ACID guarantees
---------------
* ``get_by_id_for_update`` acquires a row-level lock (SELECT … FOR UPDATE) on
  the ``communities`` row before any counter update to prevent lost-update races.
* Join table inserts use ``INSERT … ON CONFLICT DO NOTHING``, making them
  idempotent without a prior SELECT.
* The session is committed/rolled back by the ``get_db`` FastAPI dependency, so
  every mutating call either fully persists or fully reverts.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update as sql_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from community.models.community import (
    Community,
    CommunityJoinRequest,
    CommunityMember,
    CommunityType,
)


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
        """Fetch the community row and lock it (SELECT … FOR UPDATE).

        Must be called before any counter update to prevent concurrent requests
        racing on member_count / post_count.
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
        """Return all communities the given user is an active member of (paginated)."""
        uid = uuid.UUID(user_id)
        member_subq = (
            select(CommunityMember.community_id)
            .where(CommunityMember.user_id == uid)
            .scalar_subquery()
        )
        condition = Community.id.in_(member_subq)

        total = (
            await self.db.execute(
                select(func.count()).select_from(Community).where(condition)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Community)
                .where(condition)
                .order_by(Community.created_at.desc())
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
        """Return all communities belonging to a given college (paginated)."""
        uid = uuid.UUID(college_id)
        condition = Community.parent_colleges.contains([uid])

        total = (
            await self.db.execute(
                select(func.count()).select_from(Community).where(condition)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Community)
                .where(condition)
                .order_by(Community.created_at.desc())
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
        """Return a paginated list of all communities."""
        query = select(Community)
        count_query = select(func.count()).select_from(Community)

        if type_filter is not None:
            query = query.where(Community.type == type_filter)
            count_query = count_query.where(Community.type == type_filter)

        total = (await self.db.execute(count_query)).scalar_one()
        items = (
            await self.db.execute(
                query.order_by(Community.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    # ------------------------------------------------------------------
    # Membership helpers — join table queries
    # ------------------------------------------------------------------

    async def is_member(self, community_id: str, user_id: str) -> bool:
        uid = uuid.UUID(user_id)
        row = (
            await self.db.execute(
                select(CommunityMember).where(
                    CommunityMember.community_id == community_id,
                    CommunityMember.user_id == uid,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def has_pending_request(self, community_id: str, user_id: str) -> bool:
        uid = uuid.UUID(user_id)
        row = (
            await self.db.execute(
                select(CommunityJoinRequest).where(
                    CommunityJoinRequest.community_id == community_id,
                    CommunityJoinRequest.user_id == uid,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def get_requested_users(self, community_id: str) -> list[uuid.UUID]:
        """Return all user UUIDs with a pending join request."""
        rows = (
            await self.db.execute(
                select(CommunityJoinRequest.user_id).where(
                    CommunityJoinRequest.community_id == community_id
                )
            )
        ).scalars().all()
        return list(rows)

    async def get_viewer_membership_map(
        self, community_ids: list[str], user_id: str
    ) -> dict[str, tuple[bool, bool]]:
        """Return {community_id: (is_member, is_requested)} for the viewer.

        Two indexed queries regardless of list size — O(1) round trips.
        """
        if not community_ids:
            return {}

        uid = uuid.UUID(user_id)

        member_ids = set(
            (
                await self.db.execute(
                    select(CommunityMember.community_id).where(
                        CommunityMember.community_id.in_(community_ids),
                        CommunityMember.user_id == uid,
                    )
                )
            ).scalars().all()
        )

        requested_ids = set(
            (
                await self.db.execute(
                    select(CommunityJoinRequest.community_id).where(
                        CommunityJoinRequest.community_id.in_(community_ids),
                        CommunityJoinRequest.user_id == uid,
                    )
                )
            ).scalars().all()
        )

        return {
            cid: (cid in member_ids, cid in requested_ids)
            for cid in community_ids
        }

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
        """Create a community and add the creator as the first member atomically."""
        community = Community(
            name=name,
            type=type,
            parent_colleges=parent_colleges or [],
            member_count=1,
        )
        self.db.add(community)
        await self.db.flush()  # materialise the generated id

        await self.db.execute(
            pg_insert(CommunityMember)
            .values(
                community_id=community.id,
                user_id=uuid.UUID(creator_user_id),
                joined_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing()
        )

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
        # ON DELETE CASCADE removes CommunityMember and CommunityJoinRequest rows.
        await self.db.delete(community)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Membership mutations
    # ------------------------------------------------------------------

    async def add_member(self, community: Community, user_id: str) -> Community:
        """Add user to community_members and increment member_count atomically.

        ON CONFLICT DO NOTHING makes this idempotent.  The counter is bumped
        only when a row was actually inserted (checked via RETURNING).
        """
        uid = uuid.UUID(user_id)

        result = await self.db.execute(
            pg_insert(CommunityMember)
            .values(
                community_id=community.id,
                user_id=uid,
                joined_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing()
            .returning(CommunityMember.community_id)
        )
        inserted = result.scalar_one_or_none() is not None

        if inserted:
            await self.db.execute(
                sql_update(Community)
                .where(Community.id == community.id)
                .values(
                    member_count=Community.member_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # Remove any pending request for this user in the same transaction
        await self.db.execute(
            delete(CommunityJoinRequest).where(
                CommunityJoinRequest.community_id == community.id,
                CommunityJoinRequest.user_id == uid,
            )
        )

        await self.db.refresh(community)
        return community

    async def remove_member(self, community: Community, user_id: str) -> Community:
        """Remove user from community_members and decrement member_count atomically."""
        uid = uuid.UUID(user_id)

        result = await self.db.execute(
            delete(CommunityMember)
            .where(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == uid,
            )
            .returning(CommunityMember.community_id)
        )
        deleted = result.scalar_one_or_none() is not None

        if deleted:
            await self.db.execute(
                sql_update(Community)
                .where(Community.id == community.id)
                .values(
                    member_count=func.greatest(Community.member_count - 1, 0),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        await self.db.refresh(community)
        return community

    async def cancel_request(self, community: Community, user_id: str) -> Community:
        """Cancel a pending join request (used by leave when only requested)."""
        uid = uuid.UUID(user_id)
        await self.db.execute(
            delete(CommunityJoinRequest).where(
                CommunityJoinRequest.community_id == community.id,
                CommunityJoinRequest.user_id == uid,
            )
        )
        await self.db.refresh(community)
        return community

    async def request_join(self, community: Community, user_id: str) -> Community:
        """Add user to community_join_requests (idempotent via ON CONFLICT DO NOTHING)."""
        uid = uuid.UUID(user_id)
        await self.db.execute(
            pg_insert(CommunityJoinRequest)
            .values(
                community_id=community.id,
                user_id=uid,
                requested_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing()
        )
        await self.db.refresh(community)
        return community

    async def reject_request(self, community: Community, user_id: str) -> Community:
        """Remove user from community_join_requests without adding to members."""
        uid = uuid.UUID(user_id)
        await self.db.execute(
            delete(CommunityJoinRequest).where(
                CommunityJoinRequest.community_id == community.id,
                CommunityJoinRequest.user_id == uid,
            )
        )
        await self.db.refresh(community)
        return community

    # ------------------------------------------------------------------
    # Post counter
    # ------------------------------------------------------------------

    async def add_post(self, community: Community, post_id: str) -> Community:
        """Append post UUID to cross-service array and increment post_count."""
        pid = uuid.UUID(post_id)
        posts = list(community.posts)
        if pid not in posts:
            posts.append(pid)
            community.posts = posts
            await self.db.execute(
                sql_update(Community)
                .where(Community.id == community.id)
                .values(
                    post_count=Community.post_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community

    async def remove_post(self, community: Community, post_id: str) -> Community:
        """Remove post UUID from cross-service array and decrement post_count."""
        pid = uuid.UUID(post_id)
        posts = list(community.posts)
        if pid in posts:
            posts.remove(pid)
            community.posts = posts
            await self.db.execute(
                sql_update(Community)
                .where(Community.id == community.id)
                .values(
                    post_count=func.greatest(Community.post_count - 1, 0),
                    updated_at=datetime.now(timezone.utc),
                )
            )
        community.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(community)
        return community
