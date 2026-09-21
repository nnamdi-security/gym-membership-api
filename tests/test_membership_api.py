from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.plan import Plan
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


def create_plan() -> Plan:
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        session.add(plan)
        session.commit()
        session.refresh(plan)

        return plan


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


def test_member_can_start_membership_subscription():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()

    token = login(member.email)

    response = client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json={
            "plan_id": plan.id,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["member_id"] == member.id
    assert body["plan_id"] == plan.id
    assert body["status"] == "pending_payment"
    assert body["start_date"] is None
    assert body["end_date"] is None


def test_member_cannot_create_membership_for_another_user():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    another_member = create_user(
        email="other@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()

    token = login(member.email)

    response = client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json={
            "plan_id": plan.id,
            "member_id": another_member.id,
        },
    )

    assert response.status_code == 422


def test_member_cannot_create_duplicate_pending_membership():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()
    token = login(member.email)

    payload = {
        "plan_id": plan.id,
    }

    first = client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json=payload,
    )

    second = client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_member_can_view_own_membership_history():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()
    token = login(member.email)

    client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json={
            "plan_id": plan.id,
        },
    )

    response = client.get(
        "/api/v1/memberships/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    memberships = response.json()

    assert len(memberships) == 1
    assert memberships[0]["member_id"] == member.id


def test_front_desk_can_create_membership_for_member():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()

    token = login(staff.email)

    response = client.post(
        "/api/v1/memberships/for-member",
        headers=auth_headers(token),
        json={
            "member_id": member.id,
            "plan_id": plan.id,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["member_id"] == member.id
    assert body["status"] == "pending_payment"


def test_staff_cannot_create_membership_for_admin_user():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    admin = create_user(
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    plan = create_plan()

    token = login(staff.email)

    response = client.post(
        "/api/v1/memberships/for-member",
        headers=auth_headers(token),
        json={
            "member_id": admin.id,
            "plan_id": plan.id,
        },
    )

    assert response.status_code == 409

    assert response.json() == {"detail": "Selected user is not a gym member"}


def test_member_cannot_use_staff_membership_endpoint():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()
    token = login(member.email)

    response = client.post(
        "/api/v1/memberships/for-member",
        headers=auth_headers(token),
        json={
            "member_id": member.id,
            "plan_id": plan.id,
        },
    )

    assert response.status_code == 403


def test_staff_can_get_membership_by_id():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    plan = create_plan()

    token = login(staff.email)

    create_response = client.post(
        "/api/v1/memberships/for-member",
        headers=auth_headers(token),
        json={
            "member_id": member.id,
            "plan_id": plan.id,
        },
    )

    membership_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/memberships/{membership_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == membership_id


def test_member_cannot_get_membership_by_id():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login(member.email)

    response = client.get(
        "/api/v1/memberships/999",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_membership_creation_rejects_missing_plan():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/memberships",
        headers=auth_headers(token),
        json={
            "plan_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Membership plan not found"}
