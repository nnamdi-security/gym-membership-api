from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.plan import Plan
from app.models.user import User, UserRole

client = TestClient(app)




def clear_data():
    with Session(engine) as session:
        session.exec(delete(Plan))
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




def test_admin_can_create_plan():
    clear_data()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login("admin@example.com")

    response = client.post(
        "/api/v1/plans",
        headers=auth_headers(token),
        json={
            "name": "Monthly",
            "price": "15000.00",
            "period_days": 30,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Monthly"
    assert Decimal(body["price"]) == Decimal("15000.00")
    assert body["period_days"] == 30





def test_member_cannot_create_plan():
    clear_data()

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login("member@example.com")

    response = client.post(
        "/api/v1/plans",
        headers=auth_headers(token),
        json={
            "name": "Monthly",
            "price": "15000.00",
            "period_days": 30,
        },
    )

    assert response.status_code == 403





def test_unauthenticated_user_cannot_list_plans():
    clear_data()

    response = client.get(
        "/api/v1/plans"
    )

    assert response.status_code == 401



def test_member_can_list_plans():
    clear_data()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    admin_token = login("admin@example.com")

    client.post(
        "/api/v1/plans",
        headers=auth_headers(admin_token),
        json={
            "name": "Monthly",
            "price": "15000.00",
            "period_days": 30,
        },
    )

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    member_token = login("member@example.com")

    response = client.get(
        "/api/v1/plans",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["name"] == "Monthly"




def test_member_can_get_plan():
    clear_data()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    admin_token = login("admin@example.com")

    create_response = client.post(
        "/api/v1/plans",
        headers=auth_headers(admin_token),
        json={
            "name": "Quarterly",
            "price": "40000.00",
            "period_days": 90,
        },
    )

    plan_id = create_response.json()["id"]

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    member_token = login("member@example.com")

    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Quarterly"




def test_get_missing_plan_returns_404():
    clear_data()

    create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login("member@example.com")

    response = client.get(
        "/api/v1/plans/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Membership plan not found"
    }




def test_admin_can_update_plan():
    clear_data()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login("admin@example.com")

    create_response = client.post(
        "/api/v1/plans",
        headers=auth_headers(token),
        json={
            "name": "Monthly",
            "price": "15000.00",
            "period_days": 30,
        },
    )

    plan_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/plans/{plan_id}",
        headers=auth_headers(token),
        json={
            "price": "17000.00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Monthly"
    assert Decimal(body["price"]) == Decimal("17000.00")
    assert body["period_days"] == 30



def test_front_desk_cannot_update_plan():
    clear_data()

    create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    token = login("frontdesk@example.com")

    response = client.patch(
        "/api/v1/plans/1",
        headers=auth_headers(token),
        json={
            "price": "18000.00",
        },
    )

    assert response.status_code == 403





def test_admin_can_delete_unused_plan():
    clear_data()

    create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    token = login("admin@example.com")

    create_response = client.post(
        "/api/v1/plans",
        headers=auth_headers(token),
        json={
            "name": "Temporary",
            "price": "5000.00",
            "period_days": 7,
        },
    )

    plan_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404