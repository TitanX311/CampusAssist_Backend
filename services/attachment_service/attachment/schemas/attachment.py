import uuid
from datetime import datetime

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    """Full attachment metadata returned by the API."""

    id: str
    uploader_user_id: uuid.UUID
    filename: str
    content_type: str
    size: int
    bucket: str
    object_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AttachmentListResponse(BaseModel):
    """Paginated list of attachments."""

    items: list[AttachmentResponse]
    total: int
    page: int
    page_size: int


class DeleteAttachmentResponse(BaseModel):
    """Result of a delete action."""

    attachment_id: str
    message: str
