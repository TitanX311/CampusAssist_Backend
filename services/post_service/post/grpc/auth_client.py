"""Lazy gRPC client for calling auth_service GetUser — used for admin checks."""
from __future__ import annotations

import logging

import grpc
from grpc import aio

from post.grpc.auth_pb2_grpc import AuthServiceStub
from post.grpc import auth_pb2

logger = logging.getLogger(__name__)

_channel: aio.Channel | None = None
_stub: AuthServiceStub | None = None


def _get_stub(target: str) -> AuthServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = aio.insecure_channel(target)
        _stub = AuthServiceStub(_channel)
    return _stub


async def get_user_type(target: str, user_id: str) -> str:
    """
    Return the live user type from the auth DB.

    Returns one of: 'USER', 'COLLEGE', 'SUPER_ADMIN'.
    Falls back to 'USER' on any gRPC error so normal requests are never blocked.
    """
    stub = _get_stub(target)
    try:
        resp = await stub.GetUser(auth_pb2.GetUserRequest(user_id=user_id))
        return resp.type if resp.found else "USER"
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC auth GetUser error: %s", exc)
        return "USER"


async def get_user(target: str, user_id: str) -> dict:
    """Return {name, picture} for the given user_id.

    Returns an empty dict on any error so callers can safely use .get().
    Empty-string proto3 defaults are normalised to None.
    """
    stub = _get_stub(target)
    try:
        resp = await stub.GetUser(auth_pb2.GetUserRequest(user_id=user_id))
        if resp.found:
            return {"name": resp.name or None, "picture": resp.picture or None}
        return {}
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC auth GetUser error: %s", exc)
        return {}


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
