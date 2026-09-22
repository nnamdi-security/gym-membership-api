from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.user import User, UserRole


client = TestClient(app)



def create_user(
    email: str,
    role: UserRole,
    password: str = "StrongPass123!",
) -> User:
    with Session(engine) as session:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


def login(
    email: str,
    password: str = "StrongPass123!",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }



def create_user(
    email: str,
    role: UserRole,
    password: str = "StrongPass123!",
) -> User:
    with Session(engine) as session:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


def login(
    email: str,
    password: str = "StrongPass123!",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }





def test_member_cannot_create_class():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 403




def test_member_cannot_create_class():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 403




def test_front_desk_cannot_create_class():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    token = login(staff.email)

    response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Yoga",
            "capacity": 20,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 403



def test_unauthenticated_user_cannot_list_classes():
    response = client.get(
        "/api/v1/classes"
    )

    assert response.status_code == 401


def test_admin_cannot_create_past_class():
    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login(admin.email)

    response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Old Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                - timedelta(hours=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 409


def test_admin_cannot_create_past_class():
    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login(admin.email)

    response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Old Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                - timedelta(hours=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 409




def test_admin_can_update_class():
    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login(admin.email)

    create_response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    class_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/classes/{class_id}",
        headers=auth_headers(token),
        json={
            "capacity": 15,
        },
    )

    assert response.status_code == 200
    assert response.json()["capacity"] == 15
    assert response.json()["name"] == "Spin"



def test_admin_can_delete_unused_class():
    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login(admin.email)

    create_response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Temporary",
            "capacity": 10,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    class_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/classes/{class_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204




def test_authenticated_user_can_view_class_board():
    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login(admin.email)

    create_response = client.post(
        "/api/v1/classes",
        headers=auth_headers(token),
        json={
            "name": "Spin",
            "capacity": 12,
            "starts_at": (
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ).isoformat(),
        },
    )

    class_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/classes/{class_id}/board",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["capacity"] == 12
    assert body["checked_in"] == 0
    assert body["remaining"] == 12
    assert body["full"] is False