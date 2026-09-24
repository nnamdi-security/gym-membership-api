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

    response = client.get("/api/v1/auth/staff-area")

    assert response.status_code == 401


def test_role_change_takes_effect_without_new_token():
    clear_users()

    user = create_user(
        email="staff@example.com",
        role=UserRole.FRONT_DESK,
    )

    token = login("staff@example.com")

    # The token currently belongs to a front desk user.
    first_response = client.get(
        "/api/v1/auth/staff-area",
        headers=auth_headers(token),
    )

    assert first_response.status_code == 200

    # Change the user's role directly in PostgreSQL.
    with Session(engine) as session:
        stored_user = session.get(User, user.id)

        assert stored_user is not None

        stored_user.role = UserRole.MEMBER

        session.add(stored_user)
        session.commit()

    # Same JWT, but current DB role is now MEMBER.
    second_response = client.get(
        "/api/v1/auth/staff-area",
        headers=auth_headers(token),
    )

    assert second_response.status_code == 403


def test_token_is_rejected_after_user_is_deleted():
    clear_users()

    user = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login("member@example.com")

    with Session(engine) as session:
        stored_user = session.get(User, user.id)

        assert stored_user is not None

        session.delete(stored_user)
        session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401
