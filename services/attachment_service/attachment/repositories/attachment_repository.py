import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from attachment.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, attachment_id: str) -> Attachment | None:
        result = await self.db.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, attachment_ids: list[str]) -> list[Attachment]:
        """Return all Attachment rows whose id is in *attachment_ids*."""
        if not attachment_ids:
            return []
        result = await self.db.execute(
            select(Attachment).where(Attachment.id.in_(attachment_ids))
        )
        return list(result.scalars().all())

    async def get_by_uploader(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Attachment], int]:
        """Return all attachments uploaded by a specific user (paginated)."""
        uid = uuid.UUID(user_id)
        condition = Attachment.uploader_user_id == uid

        total = (
            await self.db.execute(
                select(func.count()).select_from(Attachment).where(condition)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Attachment)
                .where(condition)
                .order_by(Attachment.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Attachment], int]:
        """Return all attachments (paginated), newest first. Admin use only."""
        total = (
            await self.db.execute(select(func.count()).select_from(Attachment))
        ).scalar_one()
        items = (
            await self.db.execute(
                select(Attachment)
                .order_by(Attachment.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(items), total

    # ------------------------------------------------------------------
    # Create / delete
    # ------------------------------------------------------------------

    async def create(
        self,
        uploader_user_id: str,
        filename: str,
        content_type: str,
        size: int,
        bucket: str,
        object_key: str,
    ) -> Attachment:
        attachment = Attachment(
            uploader_user_id=uuid.UUID(uploader_user_id),
            filename=filename,
            content_type=content_type,
            size=size,
            bucket=bucket,
            object_key=object_key,
        )
        self.db.add(attachment)
        await self.db.flush()
        await self.db.refresh(attachment)
        return attachment

    async def delete(self, attachment: Attachment) -> None:
        await self.db.delete(attachment)
        await self.db.flush()
