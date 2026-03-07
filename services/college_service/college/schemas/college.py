import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CreateCollegeRequest(BaseModel):
    name: str
    contact_email: EmailStr
    physical_address: str
    admin_users: list[uuid.UUID] = []


class UpdateCollegeRequest(BaseModel):
    name: str | None = None
    contact_email: EmailStr | None = None
    physical_address: str | None = None
    admin_users: list[uuid.UUID] | None = None


class CollegeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    contact_email: str
    physical_address: str
    admin_users: list[uuid.UUID]
    communities: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class CollegeListResponse(BaseModel):
    items: list[CollegeResponse]
    total: int
    page: int
    page_size: int


class DeleteCollegeResponse(BaseModel):
    college_id: str
    message: str


class AddCommunityResponse(BaseModel):
    college_id: str
    community_id: str
    message: str


class RemoveCommunityResponse(BaseModel):
    college_id: str
    community_id: str
    message: str


class CollegeUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    college_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime


class CollegeUserListResponse(BaseModel):
    items: list[CollegeUserResponse]
    total: int
    page: int
    page_size: int


class CollegeUserEnrichedResponse(BaseModel):
    """CollegeUser enriched with identity data fetched from auth_service via gRPC."""

    college_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    # Identity fields — None when auth gRPC is unreachable
    name: str | None = None
    email: str | None = None
    picture: str | None = None
    user_type: str | None = None


class CollegeUserEnrichedListResponse(BaseModel):
    items: list[CollegeUserEnrichedResponse]
    total: int
    page: int
    page_size: int


class CollegeStatsResponse(BaseModel):
    """Aggregate counts for a single college."""

    college_id: str
    community_count: int
    admin_count: int
    member_count: int


class AdminActionResponse(BaseModel):
    college_id: str
    user_id: str
    message: str
