import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.config.settings import get_settings
from community.dependencies.auth import TokenPayload, get_current_user
from community.dependencies.college_admin import require_community_college_admin
from community.grpc import college_client, notification_client
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
    "parent_colleges": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    "posts": [],
    "member_count": 1,
    "post_count": 0,
    "is_member": True,
    "is_requested": False,
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


def _with_viewer(community, is_member: bool, is_requested: bool) -> CommunityResponse:
    """Build a CommunityResponse enriched with viewer-context booleans."""
    r = CommunityResponse.model_validate(community)
    r.is_member = is_member
    r.is_requested = is_requested
    return r


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
        "The creator is automatically added as the first member.\n\n"
        "**`type`** controls join behaviour:\n"
        "- `PUBLIC` — anyone can join immediately.\n"
        "- `PRIVATE` — join requests must be approved.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {"description": "Community created", "content": {"application/json": {"example": _COMMUNITY_EXAMPLE}}},
        401: _ERROR_401,
        409: {"description": "Conflict", "content": {"application/json": {"example": {"detail": "A community with this name already exists."}}}},
    },
)
async def create_community(
    body: CreateCommunityRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityResponse:
    repo = CommunityRepository(db)
    if await repo.get_by_name(body.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A community with this name already exists.")
    community = await repo.create(
        name=body.name,
        type=body.type,
        creator_user_id=current_user.user_id,
        parent_colleges=body.parent_colleges,
    )
    # Creator is the first member
    return _with_viewer(community, is_member=True, is_requested=False)


# ---------------------------------------------------------------------------
# GET /community/my-communities
# ---------------------------------------------------------------------------

@router.get(
    "/my-communities",
    response_model=CommunityListResponse,
    summary="List my communities",
    description=(
        "Returns a paginated list of all communities where the authenticated user "
        "is an **active member**.\n\n"
        "All items will have ``is_member=true`` and ``is_requested=false`` by definition.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Paginated list of the user's communities"},
        401: _ERROR_401,
    },
)
async def get_my_communities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_member(user_id=current_user.user_id, page=page, page_size=page_size)
    # All returned communities are ones this user is a member of
    enriched = [_with_viewer(c, is_member=True, is_requested=False) for c in items]
    return CommunityListResponse(items=enriched, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# GET /community/college/{college_id}
# ---------------------------------------------------------------------------

@router.get(
    "/college/{college_id}",
    response_model=CommunityListResponse,
    summary="List communities for a college",
    description=(
        "Returns a paginated list of all communities belonging to the given college.\n\n"
        "Each item includes ``is_member`` and ``is_requested`` for the calling user — "
        "computed in **two** indexed DB queries regardless of list size (no N+1).\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={401: _ERROR_401},
)
async def list_college_communities(
    college_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_college(college_id=college_id, page=page, page_size=page_size)

    community_ids = [c.id for c in items]
    membership_map = await repo.get_viewer_membership_map(community_ids, current_user.user_id)

    enriched = [
        _with_viewer(c, *membership_map.get(c.id, (False, False)))
        for c in items
    ]
    return CommunityListResponse(items=enriched, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# GET /community/{community_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{community_id}",
    response_model=CommunityResponse,
    summary="Get a community by ID",
    description=(
        "Returns the full community object including ``is_member`` and "
        "``is_requested`` for the calling user.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Community details", "content": {"application/json": {"example": _COMMUNITY_EXAMPLE}}},
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    is_mem = await repo.is_member(community_id, current_user.user_id)
    is_req = await repo.has_pending_request(community_id, current_user.user_id)
    return _with_viewer(community, is_member=is_mem, is_requested=is_req)


# ---------------------------------------------------------------------------
# POST /community/{community_id}/join
# ---------------------------------------------------------------------------

@router.post(
    "/{community_id}/join",
    response_model=JoinCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Join or request to join a community",
    description=(
        "**PUBLIC community** → user added immediately (`status: \"joined\"`).\n\n"
        "**PRIVATE community** → join request queued (`status: \"requested\"`).\n\n"
        "**Idempotent** — calling again returns the current state without error.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Action completed — see `status` field for outcome",
            "content": {"application/json": {"examples": {
                "joined": {"value": {"community_id": "...", "status": "joined", "message": "You have joined the community."}},
                "requested": {"value": {"community_id": "...", "status": "requested", "message": "Your join request has been sent."}},
            }}},
        },
        401: _ERROR_401,
        404: _ERROR_404,
    },
)
async def join_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinCommunityResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    user_id = current_user.user_id

    # Idempotent: already a member → return current state
    if await repo.is_member(community_id, user_id):
        return JoinCommunityResponse(community_id=community_id, status="joined", message="You are already a member of this community.")

    if community.type == CommunityType.PUBLIC:
        await repo.add_member(community, user_id)
        _settings = get_settings()
        for college_id in (community.parent_colleges or []):
            await college_client.record_membership(_settings.COLLEGE_GRPC_TARGET, str(college_id), user_id)
        return JoinCommunityResponse(community_id=community_id, status="joined", message="You have joined the community.")

    # PRIVATE — idempotent: already pending
    if await repo.has_pending_request(community_id, user_id):
        return JoinCommunityResponse(community_id=community_id, status="requested", message="Your join request is already pending approval.")

    await repo.request_join(community, user_id)
    return JoinCommunityResponse(community_id=community_id, status="requested", message="Your join request has been sent. You will be added once a moderator approves it.")


# ---------------------------------------------------------------------------
# DELETE /community/{community_id}/leave
# ---------------------------------------------------------------------------

@router.delete(
    "/{community_id}/leave",
    response_model=LeaveCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave a community",
    description=(
        "Remove the authenticated user from a community.\n\n"
        "If the user only has a **pending join request**, that request is cancelled.\n\n"
        "If the user is neither a member nor has a pending request, returns `409`.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "User successfully removed or pending request cancelled"},
        401: _ERROR_401,
        404: _ERROR_404,
        409: {"description": "Conflict — user is not a member and has no pending request"},
    },
)
async def leave_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveCommunityResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    user_id = current_user.user_id

    # Cancel a pending request (user not yet a full member)
    if not await repo.is_member(community_id, user_id):
        if await repo.has_pending_request(community_id, user_id):
            await repo.cancel_request(community, user_id)
            return LeaveCommunityResponse(community_id=community_id, message="Your join request has been cancelled.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are not a member of this community.")

    await repo.remove_member(community, user_id)
    _settings = get_settings()
    for college_id in (community.parent_colleges or []):
        await college_client.remove_membership(_settings.COLLEGE_GRPC_TARGET, str(college_id), user_id)
    return LeaveCommunityResponse(community_id=community_id, message="You have left the community.")


# ---------------------------------------------------------------------------
# PATCH /community/{community_id}
# ---------------------------------------------------------------------------

@router.patch(
    "/{community_id}",
    response_model=CommunityResponse,
    summary="Update a community",
    description="Update a community's `name` and/or `type`. Only the college admin of the community's parent college (or a SUPER_ADMIN) may do this.",
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def update_community(
    community_id: str,
    body: UpdateCommunityRequest,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> CommunityResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    community = await repo.update(community, name=body.name, type=body.type)
    is_mem = await repo.is_member(community_id, current_user.user_id)
    is_req = await repo.has_pending_request(community_id, current_user.user_id)
    return _with_viewer(community, is_member=is_mem, is_requested=is_req)


# ---------------------------------------------------------------------------
# DELETE /community/{community_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{community_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a community",
    description="Permanently deletes a community. Only the college admin or SUPER_ADMIN may do this.",
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def delete_community(
    community_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")
    await repo.delete(community)
    return {"community_id": community_id, "message": "Community deleted successfully."}


# ---------------------------------------------------------------------------
# GET /community/{community_id}/requests
# ---------------------------------------------------------------------------

@router.get(
    "/{community_id}/requests",
    response_model=PendingRequestsResponse,
    summary="List pending join requests",
    description="Returns all users with a pending join request for this PRIVATE community. Only the college admin or SUPER_ADMIN may view this.",
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
    requested = await repo.get_requested_users(community_id)
    return PendingRequestsResponse(community_id=community_id, requested_users=requested, total=len(requested))


# ---------------------------------------------------------------------------
# POST /community/{community_id}/requests/{user_id}/approve
# ---------------------------------------------------------------------------

@router.post(
    "/{community_id}/requests/{user_id}/approve",
    response_model=ApproveRejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a join request",
    description="Moves `user_id` from pending requests into members. Only college admin or SUPER_ADMIN.",
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def approve_join_request(
    community_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> ApproveRejectResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    if not await repo.has_pending_request(community_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending join request found for this user.")

    # add_member atomically removes the request and inserts the membership row
    await repo.add_member(community, user_id)
    _settings = get_settings()
    for college_id in (community.parent_colleges or []):
        await college_client.record_membership(_settings.COLLEGE_GRPC_TARGET, str(college_id), user_id)
    import asyncio
    asyncio.create_task(notification_client.send(
        _settings.NOTIFICATION_GRPC_TARGET,
        user_id=user_id,
        ntype="JOIN_ACCEPTED",
        title="Join request approved",
        body=f"You are now a member of {community.name}!",
        data={"community_id": community_id},
    ))
    return ApproveRejectResponse(community_id=community_id, user_id=user_id, message="Join request approved. User is now a member.")


# ---------------------------------------------------------------------------
# DELETE /community/{community_id}/requests/{user_id}/reject
# ---------------------------------------------------------------------------

@router.delete(
    "/{community_id}/requests/{user_id}/reject",
    response_model=ApproveRejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a join request",
    description="Removes `user_id` from pending requests without adding to members.",
    responses={401: _ERROR_401, 403: {"description": "Forbidden"}, 404: _ERROR_404},
)
async def reject_join_request(
    community_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_community_college_admin),
    db: AsyncSession = Depends(get_db),
) -> ApproveRejectResponse:
    repo = CommunityRepository(db)
    community = await repo.get_by_id_for_update(community_id)
    if community is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found.")

    if not await repo.has_pending_request(community_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending join request found for this user.")

    await repo.reject_request(community, user_id)
    return ApproveRejectResponse(community_id=community_id, user_id=user_id, message="Join request rejected.")
