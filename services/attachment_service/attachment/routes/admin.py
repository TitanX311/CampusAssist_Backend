"""
Admin-only attachment management routes — gated by require_super_admin.

GET    /attachments/admin/list      — list ALL attachments (no uploader filter)
DELETE /attachments/admin/{id}      — force-delete any attachment (MinIO + DB,
                                      skips ownership check)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from attachment.config.database import get_db
from attachment.dependencies.admin import require_super_admin
from attachment.dependencies.auth import TokenPayload
from attachment.repositories.attachment_repository import AttachmentRepository
from attachment.schemas.attachment import (
    AttachmentListResponse,
    AttachmentResponse,
    DeleteAttachmentResponse,
)
from attachment.storage import minio_client as storage

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/attachments/admin", tags=["Attachments Admin"])


@admin_router.get(
    "/list",
    response_model=AttachmentListResponse,
    summary="[Admin] List all attachments",
    description="Returns every attachment regardless of uploader. Requires SUPER_ADMIN role.",
)
async def list_all_attachments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AttachmentListResponse:
    repo = AttachmentRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return AttachmentListResponse(
        items=[AttachmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.delete(
    "/{attachment_id}",
    response_model=DeleteAttachmentResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Force-delete any attachment",
    description=(
        "Removes a file from MinIO and its DB record regardless of who uploaded it. "
        "Requires SUPER_ADMIN role."
    ),
)
async def admin_delete_attachment(
    attachment_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> DeleteAttachmentResponse:
    repo = AttachmentRepository(db)
    attachment = await repo.get_by_id(attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    try:
        await storage.delete_file(attachment.object_key)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Object store error: {exc}",
        )

    await repo.delete(attachment)
    return DeleteAttachmentResponse(
        attachment_id=attachment_id,
        message="Attachment deleted by admin.",
    )
