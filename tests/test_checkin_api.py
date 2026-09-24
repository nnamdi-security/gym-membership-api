from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.gym_class import GymClass
from app.models.membership import Membership, MembershipStatus
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


def create_active_membership(
    member: User,
) -> Membership:
    with Session(engine) as session:
        plan = Plan(
            name=f"Monthly-{member.id}",
            price=Decimal("15000.00"),
            period_days=30,
        )

        session.add(plan)
        session.commit()
        session.refresh(plan)

        today = date.today()  # noqa: DTZ011

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=29),
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        return membership


def create_future_class(
    capacity: int = 12,
) -> GymClass:
    with Session(engine) as session:
        gym_class = GymClass(
            name="Spin",
            capacity=capacity,
            starts_at=(
                datetime.now(timezone.utc)  # noqa: UP017
                + timedelta(hours=2)
            ),
        )

        session.add(gym_class)
        session.commit()
        session.refresh(gym_class)

        return gym_class


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


def test_member_can_check_in():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    create_active_membership(member)

    gym_class = create_future_class()

    token = login(member.email)

    response = client.post(
        "/api/v1/checkins",
        headers=auth_headers(token),
        json={
            "class_id": gym_class.id,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["class_id"] == gym_class.id
    assert body["member_id"] == member.id


def test_member_without_active_membership_cannot_check_in():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    gym_class = create_future_class()

    token = login(member.email)

    response = client.post(
        "/api/v1/checkins",
        headers=auth_headers(token),
        json={
            "class_id": gym_class.id,
        },
    )

    assert response.status_code == 403


def test_member_cannot_check_in_twice():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    create_active_membership(member)

    gym_class = create_future_class()

    token = login(member.email)

    payload = {
        "class_id": gym_class.id,
    }

    first = client.post(
        "/api/v1/checkins",
        headers=auth_headers(token),
        json=payload,
    )

    second = client.post(
        "/api/v1/checkins",
        headers=auth_headers(token),
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_second_member_cannot_enter_full_class():
    first_member = create_user(
        email="one@example.com",
        role=UserRole.MEMBER,
    )

    second_member = create_user(
        email="two@example.com",
        role=UserRole.MEMBER,
    )

    create_active_membership(first_member)
    create_active_membership(second_member)

    gym_class = create_future_class(
        capacity=1
    )

    first_token = login(
        first_member.email
    )

    second_token = login(
        second_member.email
    )

    first = client.post(
        "/api/v1/checkins",
        headers=auth_headers(first_token),
        json={
            "class_id": gym_class.id,
        },
    )

    second = client.post(
        "/api/v1/checkins",
        headers=auth_headers(second_token),
        json={
            "class_id": gym_class.id,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409

    assert second.json() == {
        "detail": "Class session is full"
    }


def test_member_cannot_use_staff_checkin_endpoint():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/checkins/for-member",
        headers=auth_headers(token),
        json={
            "class_id": 1,
            "member_id": member.id,
        },
    )

    assert response.status_code == 403


def test_member_can_view_own_checkins():
    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    create_active_membership(member)

    gym_class = create_future_class()

    token = login(member.email)

    checkin_response = client.post(
        "/api/v1/checkins",
        headers=auth_headers(token),
        json={
            "class_id": gym_class.id,
        },
    )

    assert checkin_response.status_code == 201

    response = client.get(
        "/api/v1/checkins/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_staff_can_view_class_checkins():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    member = create_user(
        email="member@example.com",
        role=UserRole.MEMBER,
    )

    create_active_membership(member)

    gym_class = create_future_class()

    member_token = login(
        member.email
    )

    checkin_response = client.post(
        "/api/v1/checkins",
        headers=auth_headers(member_token),
        json={
            "class_id": gym_class.id,
        },
    )

    assert checkin_response.status_code == 201

    staff_token = login(
        staff.email
    )

    response = client.get(
        f"/api/v1/checkins/class/{gym_class.id}",
        headers=auth_headers(staff_token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1