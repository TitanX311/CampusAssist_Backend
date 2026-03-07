"""
Attachment routes for attachment_service.

Manages file lifecycle:
  1. POST  /api/attachments/upload          — upload a file to MinIO, store metadata
  2. GET   /api/attachments/{id}            — get attachment metadata
  3. GET   /api/attachments/{id}/download   — stream the file from MinIO to the client
  4. GET   /api/attachments/my              — list the caller's own attachments
  5. DELETE /api/attachments/{id}           — delete from MinIO + DB (uploader only)

All endpoints require a valid Bearer access token.

The returned `id` (UUID string) is what other services (post_service, etc.)
store in their UUID arrays to reference this attachment.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from attachment.config.database import get_db
from attachment.config.settings import get_settings
from attachment.dependencies.auth import TokenPayload, get_current_user
from attachment.repositories.attachment_repository import AttachmentRepository
from attachment.schemas.attachment import (
    AttachmentListResponse,
    AttachmentResponse,
    DeleteAttachmentResponse,
)
from attachment.storage import minio_client as storage

router = APIRouter(prefix="/attachments", tags=["Attachments"])

_ATTACHMENT_EXAMPLE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "uploader_user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "photo.jpg",
    "content_type": "image/jpeg",
    "size": 204800,
    "bucket": "campus-assist",
    "object_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890/550e8400-e29b-41d4-a716-446655440000/photo.jpg",
    "created_at": "2026-03-01T10:00:00+00:00",
}

_ERROR_401 = {
    "description": "Unauthorized — missing, expired, or invalid Bearer access token",
    "content": {"application/json": {"example": {"detail": "Not authenticated."}}},
}
_ERROR_403 = {
    "description": "Forbidden — only the uploader can perform this action",
    "content": {"application/json": {"example": {"detail": "You can only manage your own attachments."}}},
}
_ERROR_404 = {
    "description": "Not Found — attachment with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Attachment not found."}}},
}
_ERROR_413 = {
    "description": "Payload Too Large — file exceeds the configured size limit",
    "content": {"application/json": {"example": {"detail": "File exceeds the 50 MB size limit."}}},
}


# ---------------------------------------------------------------------------
# POST /attachments/upload — upload a file
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description=(
        "Upload a file to the object store (MinIO) and receive back an attachment "
        "metadata object whose `id` (UUID) can be stored in post or comment records.\n\n"
        f"**Size limit:** configurable via `MAX_UPLOAD_SIZE_MB` (default 50 MB).\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {
            "description": "Attachment uploaded successfully",
            "content": {"application/json": {"example": _ATTACHMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        413: _ERROR_413,
    },
)
async def upload_attachment(
    file: UploadFile = File(..., description="The file to upload"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    settings = get_settings()

    # Determine file size without loading everything into memory.
    # FastAPI's UploadFile wraps a SpooledTemporaryFile; we read via the
    # underlying sync file object to get the true size.
    file.file.seek(0, 2)         # seek to end (sync — SpooledTemporaryFile)
    file_size = file.file.tell()
    file.file.seek(0)            # rewind

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB size limit.",
        )

    # Build a deterministic, collision-free object key.
    upload_uuid = str(uuid.uuid4())
    safe_filename = (file.filename or "file").replace(" ", "_")
    object_key = f"{current_user.user_id}/{upload_uuid}/{safe_filename}"

    content_type = file.content_type or "application/octet-stream"

    try:
        # Pass the underlying file object directly — no full in-memory read.
        await storage.upload_file(object_key, file.file, file_size, content_type)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Object store error: {exc}",
        )

    repo = AttachmentRepository(db)
    attachment = await repo.create(
        uploader_user_id=current_user.user_id,
        filename=safe_filename,
        content_type=content_type,
        size=file_size,
        bucket=settings.MINIO_BUCKET,
        object_key=object_key,
    )
    return AttachmentResponse.model_validate(attachment)


# ---------------------------------------------------------------------------
# GET /attachments/my — list caller's own attachments
# ---------------------------------------------------------------------------

@router.get(
    "/my",
    response_model=AttachmentListResponse,
    summary="List my attachments",
    description=(
        "Returns a paginated list of all attachments uploaded by the authenticated user.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of attachments",
            "content": {
                "application/json": {
                    "example": {
                        "items": [_ATTACHMENT_EXAMPLE],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    }
                }
            },
        },
        401: _ERROR_401,
    },
)
async def list_my_attachments(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentListResponse:
    repo = AttachmentRepository(db)
    items, total = await repo.get_by_uploader(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
    return AttachmentListResponse(
        items=[AttachmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /attachments/{attachment_id} — get metadata
# ---------------------------------------------------------------------------

@router.get(
    "/{attachment_id}",
    response_model=AttachmentResponse,
    summary="Get attachment metadata",
    description=(
        "Returns the metadata record for an attachment.\n\n"
        "Use this to resolve an attachment UUID stored on a post or comment "
        "into its filename, MIME type, size, etc.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Attachment metadata",
            "content": {"application/json": {"example": _ATTACHMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        404: _ERROR_404,
    },
)
async def get_attachment(
    attachment_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    repo = AttachmentRepository(db)
    attachment = await repo.get_by_id(attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    return AttachmentResponse.model_validate(attachment)


# ---------------------------------------------------------------------------
# GET /attachments/{attachment_id}/download — stream the file
# ---------------------------------------------------------------------------

@router.get(
    "/{attachment_id}/download",
    summary="Download a file",
    description=(
        "Streams the raw file bytes from MinIO through the attachment service "
        "to the client. The response carries the original `Content-Type` and a "
        "`Content-Disposition: attachment` header so browsers trigger a download.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "File stream"},
        401: _ERROR_401,
        404: _ERROR_404,
        502: {"description": "Object store unreachable or object missing"},
    },
)
async def download_attachment(
    attachment_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    repo = AttachmentRepository(db)
    attachment = await repo.get_by_id(attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    try:
        stream = storage.download_file_stream(attachment.object_key)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Object store error: {exc}",
        )

    return StreamingResponse(
        stream,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "Content-Length": str(attachment.size),
        },
    )


# ---------------------------------------------------------------------------
# DELETE /attachments/{attachment_id} — delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{attachment_id}",
    response_model=DeleteAttachmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an attachment",
    description=(
        "Permanently removes the file from MinIO **and** deletes its metadata "
        "from the database.\n\n"
        "**Ownership required:** only the uploader can delete their own attachments.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Attachment deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "attachment_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Attachment deleted successfully.",
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404,
    },
)
async def delete_attachment(
    attachment_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeleteAttachmentResponse:
    repo = AttachmentRepository(db)
    attachment = await repo.get_by_id(attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    if (
        str(attachment.uploader_user_id) != current_user.user_id
        and current_user.user_type != "SUPER_ADMIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own attachments.",
        )

    # Stage the DB deletion first (flush — still inside the open transaction).
    # If the MinIO call below raises, the exception propagates through get_db()
    # which calls session.rollback(), restoring the DB record and keeping it
    # consistent with the still-existing file in object storage.
    await repo.delete(attachment)

    try:
        await storage.delete_file(attachment.object_key)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Object store error: {exc}",
        )

    return DeleteAttachmentResponse(attachment_id=attachment_id, message="Attachment deleted successfully.")
