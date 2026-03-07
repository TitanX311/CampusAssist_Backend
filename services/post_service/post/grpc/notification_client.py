"""
Best-effort gRPC client for notification_service.

All calls are fire-and-forget — errors are logged but never raise so that a
notification failure never breaks the primary request.
"""
from __future__ import annotations

import json
import logging

import grpc.aio

from post.grpc.notification_pb2 import SendNotificationRequest, SendBulkNotificationRequest
from post.grpc.notification_pb2_grpc import NotificationServiceStub

logger = logging.getLogger(__name__)

_channel: grpc.aio.Channel | None = None
_stub: NotificationServiceStub | None = None


def _get_stub(target: str) -> NotificationServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = grpc.aio.insecure_channel(target)
        _stub = NotificationServiceStub(_channel)
    return _stub


async def send(
    target: str,
    *,
    user_id: str,
    ntype: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> None:
    """Send a single notification. Never raises."""
    try:
        stub = _get_stub(target)
        await stub.SendNotification(SendNotificationRequest(
            user_id=user_id,
            type=ntype,
            title=title,
            body=body,
            data_json=json.dumps(data) if data else "",
        ))
    except Exception as exc:
        logger.warning("SendNotification failed (%s → %s): %s", ntype, user_id, exc)


async def send_bulk(
    target: str,
    notifications: list[dict],
) -> None:
    """Send multiple notifications in one gRPC call. Never raises."""
    if not notifications:
        return
    try:
        stub = _get_stub(target)
        items = [
            SendNotificationRequest(
                user_id=n["user_id"],
                type=n["type"],
                title=n["title"],
                body=n["body"],
                data_json=json.dumps(n.get("data") or {}),
            )
            for n in notifications
        ]
        await stub.SendBulkNotification(SendBulkNotificationRequest(notifications=items))
    except Exception as exc:
        logger.warning("SendBulkNotification failed: %s", exc)


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
