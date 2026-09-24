import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)


class FakeUserRepository:
    def __init__(self):
        self.users = []
        self.next_id = 1

    def get_by_email(self, email: str):
        for user in self.users:
            if user.email == email:
                return user

        return None

    def create(self, user: User):
        user.id = self.next_id
        self.next_id += 1
        self.users.append(user)

        return user


def test_register_creates_member_with_hashed_password():
    repository = FakeUserRepository()
    service = AuthService(repository)

    user = service.register(
        UserRegisterRequest(
            email="member@example.com",
            password="StrongPass123!",
        )
    )

    assert user.id is not None
    assert user.email == "member@example.com"
    assert user.role == UserRole.MEMBER
    assert user.password_hash != "StrongPass123!"


def test_register_rejects_duplicate_email():
    repository = FakeUserRepository()
    service = AuthService(repository)

    data = UserRegisterRequest(
        email="member@example.com",
        password="StrongPass123!",
    )

    service.register(data)

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(data)


def test_authenticate_returns_access_token_for_valid_credentials():
    repository = FakeUserRepository()
    service = AuthService(repository)

    service.register(
        UserRegisterRequest(
            email="member@example.com",
            password="StrongPass123!",
        )
    )

    token = service.authenticate(
        UserLoginRequest(
            email="member@example.com",
            password="StrongPass123!",
        )
    )

    assert isinstance(token, str)
    assert token


def test_authenticate_rejects_unknown_email():
    repository = FakeUserRepository()
    service = AuthService(repository)

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(
            UserLoginRequest(
                email="missing@example.com",
                password="StrongPass123!",
            )
        )


def test_authenticate_rejects_wrong_password():
    repository = FakeUserRepository()
    service = AuthService(repository)

    service.register(
        UserRegisterRequest(
            email="member@example.com",
            password="StrongPass123!",
        )
    )

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(
            UserLoginRequest(
                email="member@example.com",
                password="WrongPass123!",
            )
        )


# FAKE REPOSITORY
class DuplicateRaceRepository:
    def get_by_email(self, email: str):
        # Simulates another request creating the user
        # after our initial lookup.
        return None

    def create(self, user: User):
        raise IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception("duplicate key"),
        )


def test_register_converts_database_duplicate_to_domain_error():
    repository = DuplicateRaceRepository()
    service = AuthService(repository)

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(
            UserRegisterRequest(
                email="member@example.com",
                password="StrongPass123!",
            )
        )
