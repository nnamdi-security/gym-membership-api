from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_session
from app.models.user import User, UserRole
from app.repositories.checkins_repository import CheckinRepository
from app.repositories.gym_class_repository import GymClassRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user import UserRepository
from app.schemas.checkin import (
    CheckinCreateRequest,
    CheckinForMemberRequest,
    CheckinResponse,
)
from app.services.checkin_service import (
    ActiveMembershipRequiredError,
    AlreadyCheckedInError,
    CheckinService,
    GymClassAlreadyStartedError,
    GymClassFullError,
    GymClassNotFoundError,
    InvalidMemberRoleError,
    MemberNotFoundError,
)


router = APIRouter(
    prefix="/checkins",
    tags=["Check-ins"],
)


SESSION_DEPENDENCY = Depends(get_session)

MEMBER_USER_DEPENDENCY = Depends(
    require_roles(UserRole.MEMBER)
)

STAFF_USER_DEPENDENCY = Depends(
    require_roles(
        UserRole.FRONT_DESK,
        UserRole.ADMIN,
    )
)




# Service dependency
def get_checkin_service(
    session: Session = SESSION_DEPENDENCY,
) -> CheckinService:
    return CheckinService(
        session=session,
        checkin_repository=CheckinRepository(session),
        gym_class_repository=GymClassRepository(session),
        membership_repository=MembershipRepository(session),
        user_repository=UserRepository(session),
    )


CHECKIN_SERVICE_DEPENDENCY = Depends(
    get_checkin_service
)



# Member self-checkin-in
@router.post(
    "",
    response_model=CheckinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check into a class session",
)
def create_checkin(
    data: CheckinCreateRequest,
    current_user: User = MEMBER_USER_DEPENDENCY,
    service: CheckinService = CHECKIN_SERVICE_DEPENDENCY,
):
    try:
        return service.check_in(
            class_id=data.class_id,
            member_id=current_user.id,
        )

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None

    except ActiveMembershipRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An active membership is required to check in",
        ) from None

    except AlreadyCheckedInError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member is already checked into this class",
        ) from None

    except GymClassFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session is full",
        ) from None

    except GymClassAlreadyStartedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session has already started",
        ) from None



# Staff-assisted checkin
@router.post(
    "/for-member",
    response_model=CheckinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check a member into a class session",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def create_checkin_for_member(
    data: CheckinForMemberRequest,
    service: CheckinService = CHECKIN_SERVICE_DEPENDENCY,
):
    try:
        return service.check_in(
            class_id=data.class_id,
            member_id=data.member_id,
        )

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None

    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        ) from None

    except InvalidMemberRoleError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selected user is not a gym member",
        ) from None

    except ActiveMembershipRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member does not have an active membership",
        ) from None

    except AlreadyCheckedInError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member is already checked into this class",
        ) from None

    except GymClassFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session is full",
        ) from None

    except GymClassAlreadyStartedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session has already started",
        ) from None





# Member view own check-ins
@router.get(
    "/me",
    response_model=list[CheckinResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my class check-in history",
)
def get_my_checkins(
    current_user: User = MEMBER_USER_DEPENDENCY,
    service: CheckinService = CHECKIN_SERVICE_DEPENDENCY,
):
    return service.get_member_checkins(
        current_user.id
    )



# Staff/admin views class attendance
@router.get(
    "/class/{class_id}",
    response_model=list[CheckinResponse],
    status_code=status.HTTP_200_OK,
    summary="List check-ins for a class session",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def get_class_checkins(
    class_id: int,
    service: CheckinService = CHECKIN_SERVICE_DEPENDENCY,
):
    try:
        return service.get_class_checkins(
            class_id
        )

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None