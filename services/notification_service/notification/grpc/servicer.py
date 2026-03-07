"""
gRPC servicer for notification_service.

Handles:
  SendNotification     — persist one notification + WS push
  SendBulkNotification — persist many notifications + WS push

Listens on a separate gRPC port (default 50056).

ACID notes
----------
Each RPC opens its own AsyncSession, calls repo.create(), then commits.
The WS push happens AFTER the commit so the client can immediately query
the REST API for the same notification — it will always exist.
"""

import logging

from notification.config.database import AsyncSessionLocal
from notification.grpc.notification_pb2 import (
    SendBulkNotificationResponse,
    SendNotificationResponse,
)
from notification.grpc.notification_pb2_grpc import NotificationServiceServicer
from notification.repositories.notification_repository import NotificationRepository
from notification.ws.manager import ws_manager

logger = logging.getLogger(__name__)


class NotificationServicer(NotificationServiceServicer):
    """Implements the NotificationService gRPC contract."""

    async def SendNotification(self, request, context):
        user_id   = request.user_id
        ntype     = request.type
        title     = request.title
        body      = request.body
        data_json = request.data_json or None

        try:
            async with AsyncSessionLocal() as session:
                repo = NotificationRepository(session)
                n = await repo.create(
                    user_id=user_id,
                    type=ntype,
                    title=title,
                    body=body,
                    data=data_json,
                )
                await session.commit()

            # Best-effort WS push (after commit — DB is the source of truth)
            await ws_manager.push(user_id, {
                "id":         str(n.id),
                "type":       n.type.value,
                "title":      n.title,
                "body":       n.body,
                "data":       n.data,
                "read":       n.read,
                "created_at": n.created_at.isoformat(),
            })

            return SendNotificationResponse(
                success=True,
                notification_id=str(n.id),
                message="",
            )

        except Exception as exc:
            logger.exception("SendNotification failed for user %s: %s", user_id, exc)
            return SendNotificationResponse(
                success=False,
                notification_id="",
                message=str(exc),
            )

    async def SendBulkNotification(self, request, context):
        count = 0
        errors: list[str] = []

        for item in request.notifications:
            user_id   = item.user_id
            ntype     = item.type
            title     = item.title
            body      = item.body
            data_json = item.data_json or None

            try:
                async with AsyncSessionLocal() as session:
                    repo = NotificationRepository(session)
                    n = await repo.create(
                        user_id=user_id,
                        type=ntype,
                        title=title,
                        body=body,
                        data=data_json,
                    )
                    await session.commit()

                await ws_manager.push(user_id, {
                    "id":         str(n.id),
                    "type":       n.type.value,
                    "title":      n.title,
                    "body":       n.body,
                    "data":       n.data,
                    "read":       n.read,
                    "created_at": n.created_at.isoformat(),
                })
                count += 1

            except Exception as exc:
                logger.exception("Bulk notify failed for user %s: %s", user_id, exc)
                errors.append(f"{user_id}: {exc}")

        success = len(errors) == 0
        message = "; ".join(errors) if errors else ""
        return SendBulkNotificationResponse(success=success, count=count, message=message)
