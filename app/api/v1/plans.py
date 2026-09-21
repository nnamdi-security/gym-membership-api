from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.db.session import get_session
from app.models.user import UserRole
from app.repositories.plan_repository import PlanRepository
from app.schemas.plan import (
    PlanCreateRequest,
    PlanResponse,
    PlanUpdateRequest,
)
from app.services.plan_service import (
    PlanInUseError,
    PlanNotFoundError,
    PlanService,
)

router = APIRouter(
    prefix="/plans",
    tags=["Membership Plans"],
)

SESSION_DEPENDENCY = Depends(get_session)


def get_plan_service(
    session: Session = SESSION_DEPENDENCY,
) -> PlanService:
    repository = PlanRepository(session)
    return PlanService(repository)


PLAN_SERVICE_DEPENDENCY = Depends(get_plan_service)
CURRENT_USER_DEPENDENCY = Depends(get_current_user)
ADMIN_USER_DEPENDENCY = Depends(require_roles(UserRole.ADMIN))


@router.get(
    "",
    response_model=list[PlanResponse],
    status_code=status.HTTP_200_OK,
    summary="List membership plans",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def list_plans(service: PlanService = PLAN_SERVICE_DEPENDENCY):
    return service.list_plans()


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a membership plan",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
def get_plan(plan_id: int, service: PlanService = PLAN_SERVICE_DEPENDENCY):
    try:
        return service.get_plan(plan_id)
    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a membership plan",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def create_plan(
    data: PlanCreateRequest, service: PlanService = PLAN_SERVICE_DEPENDENCY
):
    return service.create_plan(data)


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a membership plan",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def update_plan(
    plan_id: int,
    data: PlanUpdateRequest,
    service: PlanService = PLAN_SERVICE_DEPENDENCY,
):
    try:
        return service.update_plan(
            plan_id,
            data,
        )
    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an unused membership plan",
    dependencies=[ADMIN_USER_DEPENDENCY],
)
def delete_plan(plan_id: int, service: PlanService = PLAN_SERVICE_DEPENDENCY):
    try:
        service.delete_plan(plan_id)
    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )
    except PlanInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership plan is already in use and cannot be deleted",
        )
