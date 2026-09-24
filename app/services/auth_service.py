from sqlalchemy.exc import IntegrityError

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(self, data: UserRegisterRequest) -> User:
        existing_user = self.user_repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            email=str(data.email),
            password_hash=hash_password(data.password),
            role=UserRole.MEMBER,
        )

        try:
            return self.user_repository.create(user)
        except IntegrityError:
            raise EmailAlreadyRegisteredError from None

    def authenticate(self, data: UserLoginRequest) -> str:
        user = self.user_repository.get_by_email(str(data.email))

        if user is None:
            raise InvalidCredentialsError

        if not verify_password(
            data.password,
            user.password_hash,
        ):
            raise InvalidCredentialsError

        return create_access_token(subject=str(user.id))


# LoginRequest
#      ↓
# find user by email
#      ↓
#   missing?
#      ↓
# invalid credentials

#   otherwise
#      ↓
# verify submitted password
#      ↓
#    wrong?
#      ↓
# invalid credentials

#   correct
#      ↓
# create JWT using user.id
