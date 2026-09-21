from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.db.session import get_database
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import UserResponse
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

SESSION_DEPENDENCY = Depends(get_database)
CURRENT_USER_DEPENDENCY = Depends(get_current_user)
MEMBER_AREA_DEPENDENCY = Depends(
    require_roles(
        UserRole.MEMBER,
        UserRole.FRONT_DESK,
        UserRole.ADMIN,
    )
)
STAFF_AREA_DEPENDENCY = Depends(
    require_roles(
        UserRole.FRONT_DESK,
        UserRole.ADMIN,
    )
)
ADMIN_AREA_DEPENDENCY = Depends(require_roles(UserRole.ADMIN))


def get_auth_service(
    # This function acts as a FastAPI dependency that assembles the service for us.
    session: Session = SESSION_DEPENDENCY,
) -> AuthService:
    repository = UserRepository(session)
    return AuthService(repository)


AUTH_SERVICE_DEPENDENCY = Depends(get_auth_service)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new gym member",
    description=(
        "Create a new FitPro member account. "
        "Public registration always creates a MEMBER role."
    ),
)
def register(
    data: UserRegisterRequest,
    service: AuthService = AUTH_SERVICE_DEPENDENCY,
):
    try:
        return service.register(data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive an access token",
    description=(
        "Validate the supplied email and password and return a bearer JWT access token."
    ),
)
def login(
    data: UserLoginRequest,
    service: AuthService = AUTH_SERVICE_DEPENDENCY,
):
    try:
        token = service.authenticate(data)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current authenticated user",
    description=(
        "Return the current user identified by the supplied bearer access token."
    ),
)
def get_me(
    current_user: User = CURRENT_USER_DEPENDENCY,
):
    return current_user


# TEMPORARY ROLE-CHECK ENDPOINTS  -- REMOVE LATER
@router.get(
    "/member-area",
    summary="Example endpoint for authenticated members",
)
def member_area(
    current_user: User = MEMBER_AREA_DEPENDENCY,
):
    return {
        "message": "Member area access granted",
        "user_id": current_user.id,
    }


@router.get(
    "/staff-area",
    summary="Example endpoint for front desk and admin users",
)
def staff_area(
    current_user: User = STAFF_AREA_DEPENDENCY,
):
    return {
        "message": "Staff area access granted",
        "user_id": current_user.id,
    }


@router.get(
    "/admin-area",
    summary="Example endpoint for administrators only",
)
def admin_area(
    current_user: User = ADMIN_AREA_DEPENDENCY,
):
    return {
        "message": "Admin area access granted",
        "user_id": current_user.id,
    }


# THE AUTHENTICATION FLOW
# 1. user logs in
# 2. service verifies password
# 3. server issues JWT with sub=user.id
# 4. client sends Bearer token
# 5. HTTPBearer extracts token
# 6. decode_access_token validates signature and expiry
# 7. sub is converted to user_id
# 8. repository loads user
# 9. route receives current_user


#     HTTP REQUEST
#          │
#          ▼
#   ┌─────────────┐
#   │   Schemas   │
#   │ validation  │
#   └──────┬──────┘
#          │
#          ▼
#   ┌─────────────┐
#   │   Router    │
#   │ HTTP layer  │
#   └──────┬──────┘
#          │
#          ▼
#   ┌─────────────┐
#   │   Service   │
#   │ business    │
#   │   logic     │
#   └──────┬──────┘
#          │
#          ▼
#   ┌─────────────┐
#   │ Repository  │
#   │ persistence │
#   └──────┬──────┘
#          │
#          ▼
#    PostgreSQL
