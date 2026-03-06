"""Lazy gRPC client for communicating with college_service."""
from __future__ import annotations

import logging

import grpc
from grpc import aio

from community.grpc.college_pb2_grpc import CollegeServiceStub
from community.grpc import college_pb2

logger = logging.getLogger(__name__)

_channel: aio.Channel | None = None
_stub: CollegeServiceStub | None = None


def _get_stub(target: str) -> CollegeServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = aio.insecure_channel(target)
        _stub = CollegeServiceStub(_channel)
    return _stub


async def record_membership(target: str, college_id: str, user_id: str) -> None:
    """Tell college_service that *user_id* has joined a community of *college_id*."""
    stub = _get_stub(target)
    try:
        req = college_pb2.RecordMembershipRequest(college_id=college_id, user_id=user_id)
        resp = await stub.RecordMembership(req)
        if not resp.success:
            logger.warning("RecordMembership failed: %s", resp.message)
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC RecordMembership error: %s", exc)


async def get_college(target: str, college_id: str) -> college_pb2.GetCollegeResponse | None:
    """Fetch a college record from college_service. Returns None on gRPC error."""
    stub = _get_stub(target)
    try:
        req = college_pb2.GetCollegeRequest(college_id=college_id)
        return await stub.GetCollege(req)
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC GetCollege error: %s", exc)
        return None


async def remove_membership(target: str, college_id: str, user_id: str) -> None:
    """Tell college_service that *user_id* has left all communities of *college_id*."""
    stub = _get_stub(target)
    try:
        req = college_pb2.RemoveMembershipRequest(college_id=college_id, user_id=user_id)
        resp = await stub.RemoveMembership(req)
        if not resp.success:
            logger.warning("RemoveMembership failed: %s", resp.message)
    except grpc.aio.AioRpcError as exc:
        logger.error("gRPC RemoveMembership error: %s", exc)


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
        _channel = None
        _stub = None
