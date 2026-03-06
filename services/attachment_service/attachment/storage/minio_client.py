"""
MinIO object storage client for attachment_service.

All MinIO SDK calls are synchronous (urllib3 under the hood).  They are
wrapped with ``asyncio.get_running_loop().run_in_executor`` so they don't
block the FastAPI event loop.

Public surface:
    ensure_bucket()                           — called once during app lifespan
    upload_file(key, file_obj, size, mime)    — stream file to MinIO (no full-memory read)
    download_file_stream(key)                 — async generator of 64 KiB chunks
    delete_file(key)                          — remove object from MinIO
"""

import asyncio
from functools import partial
from typing import AsyncGenerator, BinaryIO

from minio import Minio
from minio.error import S3Error

from attachment.config.settings import get_settings


def _make_client() -> Minio:
    s = get_settings()
    return Minio(
        s.MINIO_ENDPOINT,
        access_key=s.MINIO_ACCESS_KEY,
        secret_key=s.MINIO_SECRET_KEY,
        secure=s.MINIO_SECURE,
    )


async def ensure_bucket() -> None:
    """
    Create the configured bucket if it does not already exist.
    Call this once from the FastAPI lifespan startup handler.
    """
    s = get_settings()
    client = _make_client()
    loop = asyncio.get_running_loop()

    found = await loop.run_in_executor(None, client.bucket_exists, s.MINIO_BUCKET)
    if not found:
        await loop.run_in_executor(None, client.make_bucket, s.MINIO_BUCKET)


async def upload_file(
    object_key: str,
    file_obj: BinaryIO,
    size: int,
    content_type: str,
) -> None:
    """
    Stream ``file_obj`` to MinIO at ``object_key`` without reading the
    entire file into memory first.

    Args:
        object_key:   Path inside the bucket.
        file_obj:     A readable binary file-like object (e.g. UploadFile.file).
        size:         Total byte length of the file.
        content_type: MIME type.
    """
    s = get_settings()
    client = _make_client()
    loop = asyncio.get_running_loop()

    fn = partial(
        client.put_object,
        s.MINIO_BUCKET,
        object_key,
        file_obj,
        size,
        content_type=content_type,
    )
    try:
        await loop.run_in_executor(None, fn)
    except S3Error as exc:
        raise RuntimeError(f"MinIO upload failed: {exc}") from exc


async def download_file_stream(object_key: str) -> AsyncGenerator[bytes, None]:
    """
    Async generator that streams the object in 64 KiB chunks.

    Usage::

        return StreamingResponse(
            storage.download_file_stream(attachment.object_key),
            media_type=attachment.content_type,
        )
    """
    s = get_settings()
    client = _make_client()
    loop = asyncio.get_running_loop()

    get_fn = partial(client.get_object, s.MINIO_BUCKET, object_key)
    try:
        response = await loop.run_in_executor(None, get_fn)
    except S3Error as exc:
        raise RuntimeError(f"MinIO download failed: {exc}") from exc

    try:
        while True:
            chunk = await loop.run_in_executor(None, response.read, 65536)
            if not chunk:
                break
            yield chunk
    finally:
        await loop.run_in_executor(None, response.close)
        await loop.run_in_executor(None, response.release_conn)


async def delete_file(object_key: str) -> None:
    """Remove ``object_key`` from the bucket."""
    s = get_settings()
    client = _make_client()
    loop = asyncio.get_running_loop()

    fn = partial(client.remove_object, s.MINIO_BUCKET, object_key)
    try:
        await loop.run_in_executor(None, fn)
    except S3Error as exc:
        raise RuntimeError(f"MinIO delete failed: {exc}") from exc
