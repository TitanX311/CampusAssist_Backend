import grpc

from college.grpc.college_pb2 import (
    GetCollegeResponse,
    RecordMembershipResponse,
    RemoveMembershipResponse,
)
from college.grpc.college_pb2_grpc import CollegeServiceServicer
from college.config.database import AsyncSessionLocal
from college.repositories.college_repository import CollegeRepository


class CollegeServicer(CollegeServiceServicer):
    """gRPC servicer for the CollegeService."""

    async def GetCollege(self, request, context):
        async with AsyncSessionLocal() as db:
            repo = CollegeRepository(db)
            college = await repo.get_by_id(request.college_id)
            if college is None:
                return GetCollegeResponse(found=False)
            return GetCollegeResponse(
                found=True,
                id=str(college.id),
                name=college.name,
                contact_email=college.contact_email,
                physical_address=college.physical_address,
                admin_users=[str(u) for u in (college.admin_users or [])],
                communities=[str(c) for c in (college.communities or [])],
            )

    async def RecordMembership(self, request, context):
        async with AsyncSessionLocal() as db:
            repo = CollegeRepository(db)
            college = await repo.get_by_id(request.college_id)
            if college is None:
                return RecordMembershipResponse(success=False, message="College not found.")
            try:
                await repo.record_membership(request.college_id, request.user_id)
                await db.commit()
                return RecordMembershipResponse(success=True, message="Membership recorded.")
            except Exception as exc:  # noqa: BLE001
                await db.rollback()
                return RecordMembershipResponse(success=False, message=str(exc))

    async def RemoveMembership(self, request, context):
        async with AsyncSessionLocal() as db:
            repo = CollegeRepository(db)
            try:
                await repo.remove_membership(request.college_id, request.user_id)
                await db.commit()
                return RemoveMembershipResponse(success=True, message="Membership removed.")
            except Exception as exc:  # noqa: BLE001
                await db.rollback()
                return RemoveMembershipResponse(success=False, message=str(exc))
