from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_database
from app.models.user import User, UserRole
from app.repositories.membership import MembershipRepository
from app.schemas.membership import (
    MembershipFreezeRequest,
    MembershipResponse,
    MembershipSubscribeRequest,
)
from app.services.membership_service import (
    MembershipNotFoundError,
    MembershipService,
    PlanNotFoundError,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])

SESSION_DEP = Depends(get_database)
MEMBER_USER_DEP = Depends(require_roles(UserRole.MEMBER))
FRONT_DESK_USER_DEP = Depends(require_roles(UserRole.FRONT_DESK))


def get_membership_service(
    session: Annotated[Session, SESSION_DEP],
) -> MembershipService:
    return MembershipService(MembershipRepository(session), session)


MEMBERSHIP_SERVICE_DEP = Depends(get_membership_service)


@router.post(
    "/subscriptions",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def subscribe(
    data: MembershipSubscribeRequest,
    current_user: User = MEMBER_USER_DEP,
    membership_service: MembershipService = MEMBERSHIP_SERVICE_DEP,
):
    try:
        return membership_service.subscribe(current_user.id, data)
    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )


@router.get("/me", response_model=MembershipResponse)
def get_my_membership(
    current_user: User = MEMBER_USER_DEP,
    membership_service: MembershipService = MEMBERSHIP_SERVICE_DEP,
):
    try:
        return membership_service.get_my_membership(current_user.id)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active membership found"
        )


@router.post(
    "/{membership_id}/freeze",
    response_model=MembershipResponse,
    dependencies=[FRONT_DESK_USER_DEP],
)
def freeze_membership(
    membership_id: int,
    data: MembershipFreezeRequest,
    membership_service: MembershipService = MEMBERSHIP_SERVICE_DEP,
):
    try:
        return membership_service.freeze(membership_id, data)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found"
        )


@router.post(
    "/{membership_id}/unfreeze",
    response_model=MembershipResponse,
    dependencies=[FRONT_DESK_USER_DEP],
)
def unfreeze_membership(
    membership_id: int,
    membership_service: MembershipService = MEMBERSHIP_SERVICE_DEP,
):
    try:
        return membership_service.unfreeze(membership_id)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found"
        )
