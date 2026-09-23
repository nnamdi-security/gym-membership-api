from datetime import date
from app.schemas.class_board import ClassBoardResponse

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.db.session import get_session
from app.models.user import UserRole
from app.repositories.gym_class_repository import GymClassRepository
from app.schemas.gym_class import (
    GymClassCreateRequest,
    GymClassResponse,
    GymClassUpdateRequest,
)
from app.services.gym_class_service import (
    GymClassCapacityBelowAttendanceError,
    GymClassHasCheckinsError,
    GymClassNotFoundError,
    GymClassService,
    GymClassStartsInPastError,
)

from app.core.class_board import (
    get_class_board_projector,
)
from app.core.class_board_events import (
    get_class_board_event_publisher,
)


router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)




SESSION_DEPENDENCY = Depends(get_session)

CURRENT_USER_DEPENDENCY = Depends(get_current_user)

ADMIN_USER_DEPENDENCY = Depends(
    require_roles(UserRole.ADMIN)
)


def get_gym_class_service(
    session: Session = SESSION_DEPENDENCY,
) -> GymClassService:
    repository = GymClassRepository(session)

    return GymClassService(
        repository=repository,
        class_board_projector=get_class_board_projector(),
        class_board_event_publisher=(
            get_class_board_event_publisher()
        ),
    )


GYM_CLASS_SERVICE_DEPENDENCY = Depends(
    get_gym_class_service
)



@router.get(
    "",
    response_model=list[GymClassResponse],
    status_code=status.HTTP_200_OK,
    summary="List scheduled class sessions",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def list_classes(
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    return service.list_classes()


# Get one class
@router.get(
    "/{class_id}",
    response_model=GymClassResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a scheduled class session",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def get_class(
    class_id: int,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    try:
        return service.get_class(class_id)

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None


    

# Only Admin
@router.post(
    "",
    response_model=GymClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a scheduled class session",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def create_class(
    data: GymClassCreateRequest,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    try:
        return service.create_class(data)

    except GymClassStartsInPastError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session must be scheduled in the future",
        ) from None



# Update class
@router.patch(
    "/{class_id}",
    response_model=GymClassResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a scheduled class session",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def update_class(
    class_id: int,
    data: GymClassUpdateRequest,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    try:
        return service.update_class(
            class_id,
            data,
        )

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None

    except GymClassStartsInPastError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class session must be scheduled in the future",
        ) from None

    except GymClassCapacityBelowAttendanceError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Class capacity cannot be lower than "
                "the existing check-in count"
            ),
        ) from None



# Delete class
@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an unused class session",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def delete_class(
    class_id: int,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    try:
        service.delete_class(class_id)

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None

    except GymClassHasCheckinsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Class session already has check-ins "
                "and cannot be deleted"
            ),
        ) from None



@router.get(
    "/board/by-date/{target_date}",
    response_model=list[ClassBoardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get class attendance board for a date",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def get_class_board_for_date(
    target_date: date,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    return service.get_class_board_for_date(
        target_date
    )


@router.get(
    "/{class_id}/board",
    response_model=ClassBoardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get live class attendance board",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def get_class_board(
    class_id: int,
    service: GymClassService = GYM_CLASS_SERVICE_DEPENDENCY,
):
    try:
        return service.get_class_board(
            class_id
        )

    except GymClassNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found",
        ) from None



