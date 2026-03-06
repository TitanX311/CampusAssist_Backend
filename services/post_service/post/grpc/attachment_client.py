"""
gRPC client for attachment_service.

Provides:
  validate_attachments(target, attachment_ids, user_id)
      → (valid: bool, invalid_ids: list[str])

  delete_attachments(target, attachment_ids, user_id)
      → (success: bool, message: str, failed_ids: list[str])

Both functions use a lazily-initialised insecure channel whose address is
read from settings.ATTACHMENT_GRPC_TARGET at first call.  Call `close()`
during FastAPI lifespan shutdown.
"""
import logging

import grpc
import grpc.aio

from post.grpc.attachment_pb2 import (
    ValidateAttachmentsRequest,
    DeleteAttachmentsRequest,
)
from post.grpc.attachment_pb2_grpc import AttachmentServiceStub

logger = logging.getLogger(__name__)

_channel: grpc.aio.Channel | None = None
_stub: AttachmentServiceStub | None = None


def _get_stub(target: str) -> AttachmentServiceStub:
    global _channel, _stub
    if _channel is None:
        _channel = grpc.aio.insecure_channel(target)
        _stub = AttachmentServiceStub(_channel)
    return _stub  # type: ignore[return-value]


async def validate_attachments(
    target: str,
    attachment_ids: list[str],
    user_id: str,
) -> tuple[bool, list[str]]:
    """
    Returns (valid, invalid_ids).
    `valid` is True only if every id exists and belongs to `user_id`.
    """
    stub = _get_stub(target)
    try:
        response = await stub.ValidateAttachments(
            ValidateAttachmentsRequest(attachment_ids=attachment_ids, user_id=user_id)
        )
        return response.valid, list(response.invalid_ids)
    except grpc.aio.AioRpcError as exc:
        logger.error("validate_attachments gRPC error: %s", exc)
        raise


async def delete_attachments(
    target: str,
    attachment_ids: list[str],
    user_id: str,
) -> tuple[bool, str, list[str]]:
    """
    Returns (success, message, failed_ids).
    """
    stub = _get_stub(target)
    try:
        response = await stub.DeleteAttachments(
            DeleteAttachmentsRequest(attachment_ids=attachment_ids, user_id=user_id)
        )
        return response.success, response.message, list(response.failed_ids)
    except grpc.aio.AioRpcError as exc:
        logger.error("delete_attachments gRPC error: %s", exc)
        raise


async def close() -> None:
    """Close the shared gRPC channel (call from FastAPI lifespan shutdown)."""
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
