import pytest
from pydantic import ValidationError

from app.models.user import UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse


def test_register_request_accepts_valid_input():
    data = RegisterRequest(
        email="member@example.com",
        password="StrongPass123!",
    )

    assert data.email == "member@example.com"
    assert data.password == "StrongPass123!"


def test_register_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="StrongPass123!",
        )


def test_register_request_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="member@example.com",
            password="short",
        )


def test_login_request_accepts_valid_input():
    data = LoginRequest(
        email="member@example.com",
        password="StrongPass123!",
    )

    assert data.email == "member@example.com"


def test_token_response_defaults_to_bearer():
    response = TokenResponse(
        access_token="test-token",
    )

    assert response.access_token == "test-token"
    assert response.token_type == "bearer"


def test_user_response_contains_safe_public_fields():
    response = UserResponse(
        id=1,
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    assert response.id == 1
    assert response.email == "member@example.com"
    assert response.role == UserRole.MEMBER