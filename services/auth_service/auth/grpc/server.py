"""gRPC server runner for auth_service (port 50051)."""
import logging

import grpc
import grpc.aio

from auth.grpc.servicer import AuthServicer
from auth.grpc.auth_pb2_grpc import add_AuthServiceServicer_to_server

logger = logging.getLogger(__name__)
_server: grpc.aio.Server | None = None


async def serve(port: int) -> None:
    global _server
    _server = grpc.aio.server()
    add_AuthServiceServicer_to_server(AuthServicer(), _server)
    _server.add_insecure_port(f"[::]:{port}")
    await _server.start()
    logger.info("Auth gRPC server listening on port %d", port)


async def stop() -> None:
    global _server
    if _server is not None:
        await _server.stop(grace=5)
        _server = None
        logger.info("Auth gRPC server stopped")
