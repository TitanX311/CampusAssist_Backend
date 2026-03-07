"""
Notification REST + WebSocket routes.

REST endpoints (all require ``Authorization: Bearer <token>``):

  GET    /api/notifications              — paginated notification list
  GET    /api/notifications/unread-count — number of unread notifications
  POST   /api/notifications/{id}/read   — mark one notification as read
  POST   /api/notifications/read-all    — mark ALL notifications as read
  DELETE /api/notifications/{id}        — delete one notification

WebSocket endpoint (token passed as query parameter):

  WS /api/notifications/ws?token=<jwt>

  Protocol
  --------
  * Connect with a valid JWT access token in the ``?token=`` query string.
  * The server pushes notification objects as JSON messages whenever a new
    notification is created for the authenticated user via the gRPC
    ``SendNotification`` or ``SendBulkNotification`` RPCs.

    Message shape:
      {
        "id":         "<uuid>",
        "type":       "LIKE_POST",        // see NotificationType
        "title":      "Someone liked your post",
        "body":       "...",
        "data":       { ... },            // arbitrary JSON; may be null
        "read":       false,
        "created_at": "2026-03-07T10:00:00+00:00"
      }

  * The client MAY send ``"ping"`` text frames; the server replies ``"pong"``.
  * If the token is invalid the server closes with code 4001.
  * The WebSocket connection does NOT replace the REST API — it is an
    optimistic fast-path for foreground delivery.  Notifications are always
    persisted to Postgres regardless of WS state.

  Android integration notes
  -------------------------
  * Use the WebSocket when the app is in the foreground (real-time badge
    updates, in-app notification trays).
  * When the app is backgrounded, rely on polling ``GET /api/notifications``
    after resuming, or integrate Firebase Cloud Messaging (FCM) by storing
    an FCM device token via a future ``POST /api/notifications/device-token``
    endpoint (stub described in docs).
  * Reconnect with exponential back-off on disconnect; the server does not
    guarantee message re-delivery across reconnects — use REST on reconnect
    to sync the missed notifications.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from notification.config.database import get_db
from notification.dependencies.auth import TokenPayload, decode_token, get_current_user
from notification.repositories.notification_repository import NotificationRepository
from notification.schemas.notification import (
    DeleteNotificationResponse,
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from notification.ws.manager import ws_manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_ERR_401 = {"description": "Missing / invalid Bearer token"}
_ERR_404 = {"description": "Notification not found or belongs to another user"}


# ---------------------------------------------------------------------------
# GET /api/notifications
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List notifications",
    description=(
        "Returns a paginated list of notifications for the authenticated user, "
        "newest first.\n\n"
        "Pass `?unread_only=true` to filter to unread notifications only.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` required."
    ),
    responses={200: {"description": "Paginated notifications"}, 401: _ERR_401},
)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    repo = NotificationRepository(db)
    items, total = await repo.get_by_user(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=[NotificationResponse.from_orm_obj(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /api/notifications/unread-count
# ---------------------------------------------------------------------------

@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count",
    description=(
        "Returns the number of unread notifications for the authenticated user.\n\n"
        "Useful for badge counters without fetching the full list.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` required."
    ),
    responses={200: {"description": "Unread count"}, 401: _ERR_401},
)
async def unread_count(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    repo = NotificationRepository(db)
    count = await repo.get_unread_count(current_user.user_id)
    return UnreadCountResponse(unread_count=count)


# ---------------------------------------------------------------------------
# POST /api/notifications/{notification_id}/read
# ---------------------------------------------------------------------------

@router.post(
    "/{notification_id}/read",
    response_model=MarkReadResponse,
    summary="Mark a notification as read",
    description=(
        "Marks the specified notification as read.\n\n"
        "Idempotent — calling it on an already-read notification is safe.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` required."
    ),
    responses={
        200: {"description": "Notification marked as read"},
        401: _ERR_401,
        404: _ERR_404,
    },
)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarkReadResponse:
    repo = NotificationRepository(db)
    n = await repo.mark_read(notification_id, current_user.user_id)
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return MarkReadResponse(id=str(n.id), read=n.read)


# ---------------------------------------------------------------------------
# POST /api/notifications/read-all
# ---------------------------------------------------------------------------

@router.post(
    "/read-all",
    response_model=MarkAllReadResponse,
    summary="Mark all notifications as read",
    description=(
        "Marks **all** unread notifications for the authenticated user as read "
        "in a single DB statement.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` required."
    ),
    responses={200: {"description": "All notifications marked as read"}, 401: _ERR_401},
)
async def mark_all_read(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadResponse:
    repo = NotificationRepository(db)
    updated = await repo.mark_all_read(current_user.user_id)
    return MarkAllReadResponse(updated=updated)


# ---------------------------------------------------------------------------
# DELETE /api/notifications/{notification_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{notification_id}",
    response_model=DeleteNotificationResponse,
    summary="Delete a notification",
    description=(
        "Permanently deletes the specified notification.\n\n"
        "Only the notification's recipient can delete it — the `user_id` is "
        "checked in the SQL `WHERE` clause, not just in application logic.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` required."
    ),
    responses={
        200: {"description": "Notification deleted"},
        401: _ERR_401,
        404: _ERR_404,
    },
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeleteNotificationResponse:
    repo = NotificationRepository(db)
    deleted = await repo.delete(notification_id, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return DeleteNotificationResponse(id=str(notification_id))


# ---------------------------------------------------------------------------
# WebSocket  /api/notifications/ws?token=<jwt>
# ---------------------------------------------------------------------------

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Real-time notification stream via WebSocket.

    Connect with a valid access token in the ``?token=`` query string.
    The server pushes notification JSON objects whenever a new notification
    is enqueued for the authenticated user.

    The client may send ``"ping"`` to keep the connection alive; the server
    replies with ``"pong"``.

    Close codes:
      4001 — invalid or expired token.
    """
    # Validate the token before accepting the connection
    try:
        payload = decode_token(token)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid or expired token.")
        return

    user_id = payload.user_id
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            text = await websocket.receive_text()
            if text.strip().lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(user_id, websocket)
