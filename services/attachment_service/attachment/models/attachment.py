import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from attachment.models.base import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # The authenticated user who uploaded this file.
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Original filename as supplied by the client.
    filename: Mapped[str] = mapped_column(Text, nullable=False)

    # MIME type detected/supplied at upload time.
    content_type: Mapped[str] = mapped_column(Text, nullable=False)

    # File size in bytes.
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # MinIO bucket that holds the object.
    bucket: Mapped[str] = mapped_column(Text, nullable=False)

    # Full path inside the bucket: ``{user_id}/{upload_uuid}/{filename}``
    object_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
