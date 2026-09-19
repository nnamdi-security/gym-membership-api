from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.repositories.user import UserRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest, TokenResponse
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


def get_auth_service(    
    #This function acts as a FastAPI dependency that assembles the service for us.
    session: Session = Depends(get_session),
) -> AuthService:
    repository = UserRepository(session)
    return AuthService(repository)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new member",
)
def register(
    data: UserRegisterRequest,
    service: AuthService = Depends(get_auth_service),
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
    summary="Log in and receive an access token",
)
def login(
    data: UserLoginRequest,
    service: AuthService = Depends(get_auth_service),
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