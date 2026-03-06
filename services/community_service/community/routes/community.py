import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.config.settings import get_settings
from community.dependencies.auth import TokenPayload, get_current_user
from community.dependencies.college_admin import require_community_college_admin
from community.grpc import college_client
from community.models.community import CommunityType
from community.repositories.community_repository import CommunityRepository
from community.schemas.community import (
    ApproveRejectResponse,
    CommunityListResponse,
    CommunityResponse,
    CreateCommunityRequest,
    JoinCommunityResponse,
    LeaveCommunityResponse,
    PendingRequestsResponse,
    UpdateCommunityRequest,
)

router = APIRouter(prefix="/community", tags=["Community"])

_COMMUNITY_EXAMPLE: dict = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "CS Department",
    "type": "PUBLIC",
    "member_users": ["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    "requested_users": [],
    "parent_colleges": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    "posts": [],
    "created_at": "2026-03-01T10:00:00+00:00",
    "updated_at": "2026-03-01T10:00:00+00:00",
}

_ERROR_401 = {
    "description": "Unauthorized — missing, expired, or invalid Bearer access token",
    "content": {"application/json": {"example": {"detail": "Not authenticated."}}},
}
_ERROR_404 = {
    "description": "Not Found — community with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Community not found."}}},
}
_ERROR_409_MEMBER = {
    "description": "Conflict — user is already a member",
    "content": {"application/json": {"example": {"detail": "You are already a member of this community."}}},
}
_ERROR_409_REQUESTED = {
    "description": "Conflict — join request already pending",
    "content": {"application/json": {"example": {"detail": "You already have a pending join request for this community."}}},
}


# ---------------------------------------------------------------------------
# POST /community  — create a new community
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=CommunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a community",
    description=(
        "Create a new community. Any authenticated user may create a community.\n\n"
        "The creator is automatically added as the first `member_user`.\n\n"
        "**`type`** controls join behaviour:\n"
        "- `PUBLIC` — anyone can join immediately.\n"
        "- `PRIVATE` — join requests must be approved.\n\n"
        "**`parent_colleges`** optionally links this community to one or more "
        "college entities.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {
            "description": "Community created",
            "content": {"application/json": {"example": _COMMUNITY_EXAMPLE}},
        },
        401: _ERROR_401,
        409: {
            "description": "Conflict — a community with that name already exists",
            "content": {"application/json": {"example": {"detail": "A community with this name already exists."}}},
        },
    },
)
async def create_community(
    body: CreateCommunityRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityResponse:
    repo = CommunityRepository(db)
    if await repo.get_by_name(body.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A community with this name already exists.",
        )
    community = await repo.create(
        name=body.name,
        type=body.type,
        creator_user_id=current_user.user_id,
        parent_colleges=body.parent_colleges,
    )
    return CommunityResponse.model_validate(community)


@router.get(
    "/my-communities",
    response_model=CommunityListResponse,
    summary="List my communities",
    description=(
        "Returns a paginated list of all communities where the authenticated user "
        "is an **active member** (i.e. present in `member_users`).\n\n"
        "Communities where the user only has a **pending join request** "
        "(`requested_users`) are **not** included here.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of the user's communities",
            "content": {
                "application/json": {
                    "example": {
                        "items": [_COMMUNITY_EXAMPLE],
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
async def get_my_communities(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_member(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
    return CommunityListResponse(
        items=[CommunityResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/college/{college_id}",
    response_model=CommunityListResponse,
    summary="List communities for a college",
    description=(
        "Returns a paginated list of all communities that belong to the given "
        "college (i.e. have `college_id` in their `parent_colleges` array).\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={401: _ERROR_401},
)
async def list_college_communities(
    college_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_college(
        college_id=college_id, page=page, page_size=page_size
    )
    return CommunityListResponse(
        items=[CommunityResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    )


@router.get(
    "/{community_id}",
    response_model=CommunityResponse,
    summary="Get a community by ID",
    description=(
        "Returns the full community object for the given ID.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Community details",
            "content": {"application/json": {"example": _COMMUNITY_EXAMPLE}},
        },
        401: _ERROR_401,
        404: _ERROR_404,
    },
)
async def get_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )
    return CommunityResponse.model_validate(community)


@router.post(
    "/{community_id}/join",
    response_model=JoinCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Join or request to join a community",
    description=(
        "Attempt to join a community. Behaviour depends on the community type:\n\n"
        "**PUBLIC community** → user is added to `member_users` immediately. "
        "Response `status` field will be `\"joined\"`.\n\n"
        "**PRIVATE community** → user is added to `requested_users` (pending approval). "
        "Response `status` field will be `\"requested\"`. "
        "The user becomes a full member only after a moderator accepts the request "
        "(separate endpoint, coming soon).\n\n"
        "**Idempotency / conflict rules:**\n"
        "- Sending the request again when already a member → `409 Conflict`.\n"
        "- Sending the request again when a join request is already pending → `409 Conflict`.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Action completed — see `status` field for outcome",
            "content": {
                "application/json": {
                    "examples": {
                        "joined (PUBLIC)": {
                            "summary": "User joined a PUBLIC community immediately",
                            "value": {
                                "community_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "joined",
                                "message": "You have joined the community.",
                            },
                        },
                        "requested (PRIVATE)": {
                            "summary": "Join request submitted for a PRIVATE community",
                            "value": {
                                "community_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "requested",
                                "message": "Your join request has been sent. You will be added once a moderator approves it.",
                            },
                        },
                    }
                }
            },
        },
        401: _ERROR_401,
        404: _ERROR_404,
        409: {
            "description": "Conflict — already a member or request already pending",
            "content": {
                "application/json": {
                    "examples": {
                        "already a member": {"value": _ERROR_409_MEMBER["content"]["application/json"]["example"]},
                        "request pending": {"value": _ERROR_409_REQUESTED["content"]["application/json"]["example"]},
                    }
                }
            },
        },
    },
)
async def join_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinCommunityResponse:
    repo = CommunityRepository(db)

    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    user_id = current_user.user_id
    uid = uuid.UUID(user_id)

    # Already a member?
    if uid in community.member_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this community.",
        )

    if community.type == CommunityType.PUBLIC:
        await repo.add_member(community, user_id)
        # Notify college_service of the new membership
        _settings = get_settings()
        for college_id in (community.parent_colleges or []):
            await college_client.record_membership(
                _settings.COLLEGE_GRPC_TARGET, str(college_id), user_id
            )
        return JoinCommunityResponse(
            community_id=community_id,
            status="joined",
            message="You have joined the community.",
        )

    # PRIVATE — check if request already pending
    if uid in community.requested_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this community.",
        )

    await repo.request_join(community, user_id)
    return JoinCommunityResponse(
        community_id=community_id,
        status="requested",
        message="Your join request has been sent. You will be added once a moderator approves it.",
    )


@router.delete(
    "/{community_id}/leave",
    response_model=LeaveCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave a community",
    description=(
        "Remove the authenticated user from a community's `member_users` list.\n\n"
        "**Edge cases:**\n"
        "- If the user is not a member (including if they only have a pending join "
        "request), the request fails with `409 Conflict`. "
        "To cancel a pending join request a separate endpoint will be provided.\n"
        "- If the community does not exist, `404 Not Found` is returned.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "User successfully removed from the community",
            "content": {
                "application/json": {
                    "example": {
                        "community_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "You have left the community.",
                    }
                }
            },
        },
        401: _ERROR_401,
        404: _ERROR_404,
        409: {
            "description": "Conflict — user is not an active member of this community",
            "content": {
                "application/json": {
                    "example": {"detail": "You are not a member of this community."}
                }
            },
        },
    },
)
async def leave_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveCommunityResponse:
    repo = CommunityRepository(db)

    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    uid = uuid.UUID(current_user.user_id)

    if uid not in community.member_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are not a member of this community.",
        )

    await repo.remove_member(community, current_user.user_id)
    # Notify college_service to remove membership
    _settings = get_settings()
    for college_id in (community.parent_colleges or []):
        await college_client.remove_membership(
            _settings.COLLEGE_GRPC_TARGET, str(college_id), current_user.user_id
        )
    return LeaveCommunityResponse(
        community_id=community_id,
        message="You have left the community.",
    )


# ---------------------------------------------------------------------------
# PATCH /community/{community_id}  — update community (college admin only)
# ---------------------------------------------------------------------------

@router.patch(
    "/{community_id}",
    response_model=CommunityResponse,
    summary="Update a community",
    description=(
        "Update a community's `name` and/or `type`. Only the college admin of "
        "the community's parent college (or a SUPER_ADMIN) may do this."
    ),
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def update_community(
    community_id: str,
    body: UpdateCommunityRequest,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> CommunityResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    community = await repo.update(community, name=body.name, type=body.type)
    return CommunityResponse.model_validate(community)


# ---------------------------------------------------------------------------
# DELETE /community/{community_id}  — delete community (college admin only)
# ---------------------------------------------------------------------------

@router.delete(
    "/{community_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a community",
    description=(
        "Permanently deletes a community. Only the college admin of the "
        "community's parent college (or a SUPER_ADMIN) may do this."
    ),
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def delete_community(
    community_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    await repo.delete(community)
    return {"community_id": community_id, "message": "Community deleted successfully."}


# ---------------------------------------------------------------------------
# GET /community/{community_id}/requests  — list pending join requests
# ---------------------------------------------------------------------------

@router.get(
    "/{community_id}/requests",
    response_model=PendingRequestsResponse,
    summary="List pending join requests",
    description=(
        "Returns all users who have a pending join request for this PRIVATE "
        "community. Only the college admin of the parent college (or SUPER_ADMIN) "
        "may view this."
    ),
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def list_join_requests(
    community_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> PendingRequestsResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    return PendingRequestsResponse(
        community_id=community_id,
        requested_users=list(community.requested_users or []),
        total=len(community.requested_users or []),
    )


# ---------------------------------------------------------------------------
# POST /community/{community_id}/requests/{user_id}/approve  — approve join
# ---------------------------------------------------------------------------

@router.post(
    "/{community_id}/requests/{user_id}/approve",
    response_model=ApproveRejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a join request",
    description=(
        "Moves `user_id` from `requested_users` into `member_users`. "
        "Only the college admin of the parent college (or SUPER_ADMIN) may do this."
    ),
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def approve_join_request(
    community_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> ApproveRejectResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    uid = uuid.UUID(user_id)
    if uid not in (community.requested_users or []):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending join request found for this user.",
        )

    await repo.add_member(community, user_id)
    # Notify college_service of the new membership
    _settings = get_settings()
    for college_id in (community.parent_colleges or []):
        await college_client.record_membership(
            _settings.COLLEGE_GRPC_TARGET, str(college_id), user_id
        )
    return ApproveRejectResponse(
        community_id=community_id,
        user_id=user_id,
        message="Join request approved. User is now a member.",
    )


# ---------------------------------------------------------------------------
# DELETE /community/{community_id}/requests/{user_id}/reject  — reject join
# ---------------------------------------------------------------------------

@router.delete(
    "/{community_id}/requests/{user_id}/reject",
    response_model=ApproveRejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a join request",
    description=(
        "Removes `user_id` from `requested_users` without adding them as a member. "
        "Only the college admin of the parent college (or SUPER_ADMIN) may do this."
    ),
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def reject_join_request(
    community_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> ApproveRejectResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    uid = uuid.UUID(user_id)
    if uid not in (community.requested_users or []):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending join request found for this user.",
        )

    await repo.reject_request(community, user_id)
    return ApproveRejectResponse(
        community_id=community_id,
        user_id=user_id,
        message="Join request rejected.",
    )
