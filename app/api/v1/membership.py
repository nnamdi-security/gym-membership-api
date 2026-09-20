from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_session
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


def get_membership_service(session: Session = Depends(get_session)) -> MembershipService:
    return MembershipService(MembershipRepository(session), session)


@router.post("/subscriptions", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def subscribe(
    data: MembershipSubscribeRequest,
    current_user: User = Depends(require_roles(UserRole.MEMBER)),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        return membership_service.subscribe(current_user.id, data)
    except PlanNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")


@router.get("/me", response_model=MembershipResponse)
def get_my_membership(
    current_user: User = Depends(require_roles(UserRole.MEMBER)),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        return membership_service.get_my_membership(current_user.id)
    except MembershipNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active membership found")


@router.post("/{membership_id}/freeze", response_model=MembershipResponse)
def freeze_membership(
    membership_id: int,
    data: MembershipFreezeRequest,
    current_user: User = Depends(require_roles(UserRole.FRONT_DESK)),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        return membership_service.freeze(membership_id, data)
    except MembershipNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")


@router.post("/{membership_id}/unfreeze", response_model=MembershipResponse)
def unfreeze_membership(
    membership_id: int,
    current_user: User = Depends(require_roles(UserRole.FRONT_DESK)),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        return membership_service.unfreeze(membership_id)
    except MembershipNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")