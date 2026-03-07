from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from notification.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """A single notification as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    data: dict[str, Any] | None = None
    read: bool
    created_at: datetime

    @classmethod
    def from_orm_obj(cls, n: Any) -> "NotificationResponse":
        return cls(
            id=str(n.id),
            user_id=str(n.user_id),
            type=n.type,
            title=n.title,
            body=n.body,
            data=n.data,
            read=n.read,
            created_at=n.created_at,
        )


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    id: str
    read: bool = True


class MarkAllReadResponse(BaseModel):
    updated: int


class DeleteNotificationResponse(BaseModel):
    id: str
    message: str = "Notification deleted."
