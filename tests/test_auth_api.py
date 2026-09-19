from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db.session import engine
from app.main import app
from app.models.user import User


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