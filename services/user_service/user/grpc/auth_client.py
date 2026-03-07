"""Lazy gRPC client for calling auth_service GetUser."""
from __future__ import annotations

import logging

import grpc
from grpc import aio

from user.grpc.auth_pb2_grpc import AuthServiceStub
from user.grpc import auth_pb2

logger = logging.getLogger(__name__)

_channel: aio.Channel | None = None
_stub: AuthServiceStub | None = None


def _get_stub(target: str) -> AuthServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = aio.insecure_channel(target)
        _stub = AuthServiceStub(_channel)
    return _stub


async def get_user(target: str, user_id: str) -> dict:
    """
    Return full user info from auth_service.

    Returns a dict with keys: found, id, email, name, picture, type, is_active.
    Returns {} on any error.
    """
    stub = _get_stub(target)
    try:
        resp = await stub.GetUser(auth_pb2.GetUserRequest(user_id=user_id))
        if resp.found:
            return {
                "found": True,
                "id": resp.id,
                "email": resp.email or None,
                "name": resp.name or None,
                "picture": resp.picture or None,
                "type": resp.type or "USER",
                "is_active": resp.is_active,
            }
        return {"found": False}
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC auth GetUser error: %s", exc)
        return {}


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
