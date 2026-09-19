from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db.session import engine
from app.main import app
from app.models.user import User
from app.core.security import create_access_token
from datetime import timedelta


client = TestClient(app)


def clear_users():
    with Session(engine) as session:
        session.exec(delete(User))
        session.commit()


def test_register_user():
    clear_users()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "member@example.com"
    assert body["role"] == "member"
    assert "password_hash" not in body


def test_register_rejects_duplicate_email():
    clear_users()

    payload = {
        "email": "member@example.com",
        "password": "StrongPass123!",
    }

    first = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409

    assert second.json() == {
        "detail": "Email is already registered"
    }


def test_login_returns_access_token():
    clear_users()

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_wrong_password():
    clear_users()

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "member@example.com",
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_login_rejects_unknown_email():
    clear_users()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401


def register_and_login():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "member@example.com",
            "password": "StrongPass123!",
        },
    )

    return response.json()["access_token"]




def test_me_returns_current_user():
    clear_users()

    token = register_and_login()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "member@example.com"
    assert body["role"] == "member"


def test_me_rejects_missing_token():
    clear_users()

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Could not validate credentials"
    }


def test_me_rejects_invalid_token():
    clear_users()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer not-a-valid-token",
        },
    )

    assert response.status_code == 401


def test_me_rejects_token_for_missing_user():
    clear_users()

    token = create_access_token(
        subject="999999"
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401




def test_me_rejects_expired_token():
    clear_users()

    token = create_access_token(
        subject="1",
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401