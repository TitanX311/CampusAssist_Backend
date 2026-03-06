import asyncio
import logging

import grpc
from grpc import aio

from college.grpc.college_pb2_grpc import add_CollegeServiceServicer_to_server
from college.grpc.servicer import CollegeServicer

logger = logging.getLogger(__name__)

_server: aio.Server | None = None


async def serve(port: int = 50055) -> None:
    global _server
    _server = aio.server()
    add_CollegeServiceServicer_to_server(CollegeServicer(), _server)
    listen_addr = f"[::]:{port}"
    _server.add_insecure_port(listen_addr)
    await _server.start()
    logger.info("college gRPC server listening on %s", listen_addr)


async def stop() -> None:
    global _server
    if _server is not None:
        await _server.stop(grace=5)
        _server = None
        logger.info("college gRPC server stopped")
