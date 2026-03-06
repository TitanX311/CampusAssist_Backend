import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from college.models.college import College
from college.models.college_user import CollegeUser


class CollegeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # College look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, college_id: str) -> College | None:
        result = await self.db.execute(select(College).where(College.id == college_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> College | None:
        result = await self.db.execute(select(College).where(College.name == name))
        return result.scalar_one_or_none()

    async def get_by_admin(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[College], int]:
        """Return all colleges where user_id is in admin_users (paginated)."""
        uid = uuid.UUID(user_id)
        condition = College.admin_users.contains([uid])
        total = (
            await self.db.execute(
                select(func.count()).select_from(College).where(condition)
            )
        ).scalar_one()
        items = (
            await self.db.execute(
                select(College)
                .where(condition)
                .order_by(College.name)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    async def get_all(self, page: int = 1, page_size: int = 20) -> tuple[list[College], int]:
        total = (await self.db.execute(select(func.count()).select_from(College))).scalar_one()
        items = (
            await self.db.execute(
                select(College)
                .order_by(College.name)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    # ------------------------------------------------------------------
    # College mutations
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        contact_email: str,
        physical_address: str,
        admin_users: list[uuid.UUID],
    ) -> College:
        college = College(
            name=name,
            contact_email=contact_email,
            physical_address=physical_address,
            admin_users=admin_users,
        )
        self.db.add(college)
        await self.db.flush()
        await self.db.refresh(college)
        return college

    async def update(
        self,
        college: College,
        name: str | None,
        contact_email: str | None,
        physical_address: str | None,
        admin_users: list[uuid.UUID] | None,
    ) -> College:
        if name is not None:
            college.name = name
        if contact_email is not None:
            college.contact_email = contact_email
        if physical_address is not None:
            college.physical_address = physical_address
        if admin_users is not None:
            college.admin_users = admin_users
        college.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(college)
        return college

    async def delete(self, college: College) -> None:
        await self.db.delete(college)
        await self.db.flush()

    async def add_community(self, college: College, community_id: str) -> College:
        cid = uuid.UUID(community_id)
        if cid not in (college.communities or []):
            college.communities = list(college.communities or []) + [cid]
            college.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(college)
        return college

    async def remove_community(self, college: College, community_id: str) -> College:
        cid = uuid.UUID(community_id)
        college.communities = [c for c in (college.communities or []) if c != cid]
        college.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(college)
        return college

    async def add_admin(self, college: College, user_id: str) -> College:
        """Atomically append user_id to admin_users if not already present."""
        uid = uuid.UUID(user_id)
        admins = list(college.admin_users or [])
        if uid not in admins:
            admins.append(uid)
            college.admin_users = admins
            college.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(college)
        return college

    async def remove_admin(self, college: College, user_id: str) -> College:
        """Atomically remove user_id from admin_users."""
        uid = uuid.UUID(user_id)
        college.admin_users = [a for a in (college.admin_users or []) if a != uid]
        college.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(college)
        return college

    # ------------------------------------------------------------------
    # CollegeUser (cross-service join table)
    # ------------------------------------------------------------------

    async def record_membership(self, college_id: str, user_id: str) -> None:
        """Insert (college_id, user_id) if not already present (idempotent)."""
        cid = uuid.UUID(college_id)
        uid = uuid.UUID(user_id)
        existing = await self.db.execute(
            select(CollegeUser).where(
                CollegeUser.college_id == cid,
                CollegeUser.user_id == uid,
            )
        )
        if existing.scalar_one_or_none() is None:
            self.db.add(CollegeUser(college_id=cid, user_id=uid))
            await self.db.flush()

    async def remove_membership(self, college_id: str, user_id: str) -> None:
        """Delete (college_id, user_id) if present (idempotent)."""
        cid = uuid.UUID(college_id)
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(CollegeUser).where(
                CollegeUser.college_id == cid,
                CollegeUser.user_id == uid,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await self.db.delete(row)
            await self.db.flush()

    async def get_users(
        self, college_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[CollegeUser], int]:
        cid = uuid.UUID(college_id)
        condition = CollegeUser.college_id == cid
        total = (
            await self.db.execute(select(func.count()).select_from(CollegeUser).where(condition))
        ).scalar_one()
        items = (
            await self.db.execute(
                select(CollegeUser)
                .where(condition)
                .order_by(CollegeUser.joined_at)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total
