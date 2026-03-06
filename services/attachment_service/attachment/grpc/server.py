"""
gRPC server runner for attachment_service.

Call `serve()` from the FastAPI lifespan to start the gRPC server in the
same process alongside uvicorn.  Call `stop()` during shutdown.
"""
import logging

import grpc
import grpc.aio

from attachment.grpc.servicer import AttachmentServicer
from attachment.grpc.attachment_pb2_grpc import add_AttachmentServiceServicer_to_server

logger = logging.getLogger(__name__)

_server: grpc.aio.Server | None = None


async def serve(port: int) -> None:
    """Start the gRPC server on *port* (non-blocking — runs in background)."""
    global _server
    _server = grpc.aio.server()
    add_AttachmentServiceServicer_to_server(AttachmentServicer(), _server)
    _server.add_insecure_port(f"[::]:{port}")
    await _server.start()
    logger.info("Attachment gRPC server listening on port %d", port)


async def stop() -> None:
    """Gracefully stop the gRPC server."""
    global _server
    if _server is not None:
        await _server.stop(grace=5)
        _server = None
        logger.info("Attachment gRPC server stopped")
