from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_session
from app.models.user import User, UserRole
from app.repositories.membership_repository import MembershipRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.user_repository import UserRepository
from app.schemas.membership import (
    MembershipCreateForMemberRequest,
    MembershipCreateRequest,
    MembershipResponse,
)
from app.services.membership_service import (
    CurrentMembershipExistsError,
    InvalidMemberRoleError,
    MemberNotFoundError,
    MembershipCannotBeFrozenError,
    MembershipCannotBeUnfrozenError,
    MembershipNotFoundError,
    MembershipService,
    PendingMembershipExistsError,
    PlanNotFoundError,
)

router = APIRouter(
    prefix="/memberships",
    tags=["Memberships"],
)


SESSION_DEPENDENCY = Depends(get_session)

MEMBER_USER_DEPENDENCY = Depends(require_roles(UserRole.MEMBER))

STAFF_USER_DEPENDENCY = Depends(
    require_roles(
        UserRole.FRONT_DESK,
        UserRole.ADMIN,
    )
)


def get_membership_service(
    session: Session = SESSION_DEPENDENCY,
) -> MembershipService:
    membership_repository = MembershipRepository(session)
    plan_repository = PlanRepository(session)
    user_repository = UserRepository(session)

    return MembershipService(
        membership_repository,
        plan_repository,
        user_repository,
    )


MEMBERSHIP_SERVICE_DEPENDENCY = Depends(get_membership_service)


# Member starts their own subscription
@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a membership subscription",
    description=("Create a pending-payment membership for the authenticated member."),
)
def create_membership(
    data: MembershipCreateRequest,
    current_user: User = MEMBER_USER_DEPENDENCY,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    try:
        return service.create_for_current_member(
            member_id=current_user.id,
            data=data,
        )
    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )
    except CurrentMembershipExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member already has a current membership",
        )
    except PendingMembershipExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Member already has a membership awaiting payment"),
        )


# Member views their own history. Members use this endpoint. This prevents accidental cross-member data access.
@router.get(
    "/me",
    response_model=list[MembershipResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my membership history",
)
def get_my_memberships(
    current_user: User = MEMBER_USER_DEPENDENCY,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    return service.get_member_history(current_user.id)


# Staff creates a subscription for a member
@router.post(
    "/for-member",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a subscription for a member",
    description=(
        "Allow front-desk staff or administrators to create "
        "a pending-payment membership for another member."
    ),
    dependencies=[STAFF_USER_DEPENDENCY],
)
def create_membership_for_member(
    data: MembershipCreateForMemberRequest,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    try:
        return service.create_for_member(data)

    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    except InvalidMemberRoleError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selected user is not a gym member",
        )

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )

    except CurrentMembershipExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member already has a current membership",
        )

    except PendingMembershipExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Member already has a membership awaiting payment"),
        )


# Staff/admin retrieves one membership
@router.get(
    "/{membership_id}",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a membership",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def get_membership(
    membership_id: int,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    try:
        return service.get_membership(membership_id)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )


# staff/admin API endpoints to freeze and unfreeze memberships
@router.post(
    "/{membership_id}/freeze",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Freeze a membership",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def freeze_membership(
    membership_id: int,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    try:
        return service.freeze_membership(membership_id)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )
    except MembershipCannotBeFrozenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership cannot be frozen in its current state",
        )


@router.post(
    "/{membership_id}/unfreeze",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Unfreeze a membership",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def unfreeze_membership(
    membership_id: int,
    service: MembershipService = MEMBERSHIP_SERVICE_DEPENDENCY,
):
    try:
        return service.unfreeze_membership(membership_id)
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )
    except MembershipCannotBeUnfrozenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership cannot be unfrozen in its current state",
        )


# PENDING_PAYMENT
#     │
#     ├── blocks another pending subscription
#     │
#     ▼
# ACTIVE ────────┐
#                │ both count as the
# FROZEN ────────┘ current membership

# EXPIRED
# CANCELLED
#     ↓
# do not block a future subscription
