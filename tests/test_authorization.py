from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.user import User, UserRole


client = TestClient(app)


def clear_users():
    with Session(engine) as session:
        session.exec(delete(User))
        session.commit()


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


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }



def test_member_can_access_member_area():
    clear_users()

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login("member@example.com")

    response = client.get(
        "/api/v1/auth/member-area",
        headers=auth_headers(token),
    )

    assert response.status_code == 200




def test_member_cannot_access_staff_area():
    clear_users()

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login("member@example.com")

    response = client.get(
        "/api/v1/auth/staff-area",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "You do not have permission to perform this action"
    }





def test_front_desk_can_access_staff_area():
    clear_users()

    create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    token = login("frontdesk@example.com")

    response = client.get(
        "/api/v1/auth/staff-area",
        headers=auth_headers(token),
    )

    assert response.status_code == 200




def test_front_desk_cannot_access_admin_area():
    clear_users()

    create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    token = login("frontdesk@example.com")

    response = client.get(
        "/api/v1/auth/admin-area",
        headers=auth_headers(token),
    )

    assert response.status_code == 403





def test_admin_can_access_admin_area():
    clear_users()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login("admin@example.com")

    response = client.get(
        "/api/v1/auth/admin-area",
        headers=auth_headers(token),
    )

    assert response.status_code == 200







def test_staff_area_rejects_unauthenticated_request():
    clear_users()

    response = client.get(
        "/api/v1/auth/staff-area"
    )

    assert response.status_code == 401