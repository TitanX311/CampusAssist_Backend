"""
gRPC servicer for attachment_service.

Handles:
  ValidateAttachments — verify that all UUIDs exist and belong to a user.
  DeleteAttachments   — atomically remove a list of attachments (MinIO + DB).

Runs alongside the FastAPI/uvicorn server on a separate gRPC port (50054).
"""
import logging

import grpc

from attachment.config.database import AsyncSessionLocal
from attachment.repositories.attachment_repository import AttachmentRepository
from attachment.storage import minio_client as storage
from attachment.grpc.attachment_pb2 import (
    ValidateAttachmentsResponse,
    DeleteAttachmentsResponse,
)
from attachment.grpc.attachment_pb2_grpc import AttachmentServiceServicer

logger = logging.getLogger(__name__)


class AttachmentServicer(AttachmentServiceServicer):
    """Implements the AttachmentService gRPC contract."""

    # ------------------------------------------------------------------
    # ValidateAttachments
    # ------------------------------------------------------------------

    async def ValidateAttachments(self, request, context):
        """
        Check that every attachment_id exists in the DB and was uploaded by
        request.user_id.  Returns all IDs that fail either check in
        `invalid_ids`.
        """
        attachment_ids: list[str] = list(request.attachment_ids)
        user_id: str = request.user_id

        if not attachment_ids:
            return ValidateAttachmentsResponse(valid=True, invalid_ids=[])

        async with AsyncSessionLocal() as session:
            repo = AttachmentRepository(session)
            found = await repo.get_by_ids(attachment_ids)

        found_ids = {str(a.id) for a in found}
        invalid: list[str] = []

        for aid in attachment_ids:
            if aid not in found_ids:
                invalid.append(aid)
                continue
            # Find the matching attachment object to check ownership
            attachment = next(a for a in found if str(a.id) == aid)
            if user_id and str(attachment.uploader_user_id) != user_id:
                invalid.append(aid)

        valid = len(invalid) == 0
        return ValidateAttachmentsResponse(valid=valid, invalid_ids=invalid)

    # ------------------------------------------------------------------
    # DeleteAttachments
    # ------------------------------------------------------------------

    async def DeleteAttachments(self, request, context):
        """
        Delete each attachment from MinIO then from the DB.
        If user_id is provided, only the owner's attachments are deleted;
        attachments not belonging to user_id are skipped and reported in
        `failed_ids`.

        Implements a best-effort saga: each attachment is deleted
        independently so a single failure doesn't prevent the others from
        being cleaned up.
        """
        attachment_ids: list[str] = list(request.attachment_ids)
        user_id: str = request.user_id

        if not attachment_ids:
            return DeleteAttachmentsResponse(success=True, message="Nothing to delete.", failed_ids=[])

        failed: list[str] = []

        async with AsyncSessionLocal() as session:
            repo = AttachmentRepository(session)
            found = await repo.get_by_ids(attachment_ids)
            found_map = {str(a.id): a for a in found}

            for aid in attachment_ids:
                attachment = found_map.get(aid)
                if attachment is None:
                    logger.warning("DeleteAttachments: attachment %s not found, skipping", aid)
                    continue  # already gone — treat as success

                if user_id and str(attachment.uploader_user_id) != user_id:
                    logger.warning(
                        "DeleteAttachments: attachment %s not owned by %s, skipping",
                        aid, user_id,
                    )
                    failed.append(aid)
                    continue

                # Delete from object store first
                try:
                    await storage.delete_file(attachment.object_key)
                except Exception as exc:
                    logger.error("DeleteAttachments: MinIO delete failed for %s: %s", aid, exc)
                    failed.append(aid)
                    continue

                # Delete DB record
                try:
                    await repo.delete(attachment)
                    await session.commit()
                except Exception as exc:
                    logger.error("DeleteAttachments: DB delete failed for %s: %s", aid, exc)
                    await session.rollback()
                    failed.append(aid)

        if failed:
            return DeleteAttachmentsResponse(
                success=False,
                message=f"Failed to delete {len(failed)} attachment(s).",
                failed_ids=failed,
            )
        return DeleteAttachmentsResponse(success=True, message="All attachments deleted.", failed_ids=[])
