from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.db.session import engine
from app.main import app
from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.payment import PaymentMethod
from app.models.plan import Plan
from app.models.user import User, UserRole


client = TestClient(app)



#Helper function
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


def create_pending_membership() -> tuple[User, Plan, Membership]:
    with Session(engine) as session:
        member = User(
            email="member@example.com",
            password_hash=hash_password(
                "StrongPass123!"
            ),
            role=UserRole.MEMBER,
        )

        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        session.add(member)
        session.add(plan)
        session.commit()

        session.refresh(member)
        session.refresh(plan)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.PENDING_PAYMENT,
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        return member, plan, membership


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


def test_front_desk_can_record_payment():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, plan, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    response = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["membership_id"] == membership.id
    assert Decimal(body["amount"]) == plan.price
    assert body["status"] == "succeeded"
    assert body["method"] == "cash"
    assert body["recorded_by"] == staff.id
    assert body["paid_at"] is not None



def test_staff_payment_activates_membership():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, _, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    response = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.TRANSFER.value,
        },
    )

    assert response.status_code == 201

    with Session(engine) as session:
        stored = session.get(
            Membership,
            membership.id,
        )

        assert stored is not None
        assert (
            stored.status
            == MembershipStatus.ACTIVE
        )
        assert stored.start_date is not None
        assert stored.end_date is not None





def test_member_cannot_record_staff_payment():
    member, _, membership = (
        create_pending_membership()
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 403




def test_staff_cannot_record_online_payment_manually():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, _, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    response = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.ONLINE.value,
        },
    )

    assert response.status_code == 422



def test_membership_cannot_be_paid_twice():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, _, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    payload = {
        "membership_id": membership.id,
        "method": PaymentMethod.CASH.value,
    }

    first = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json=payload,
    )

    second = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json=payload,
    )

    assert first.status_code == 201

    # The first successful payment activates the membership,
    # so the second request no longer sees PENDING_PAYMENT.
    assert second.status_code == 409



def test_staff_can_get_payment():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, _, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    create_response = client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.CARD.value,
        },
    )

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id



def test_staff_can_view_membership_payment_history():
    staff = create_user(
        email="frontdesk@example.com",
        role=UserRole.FRONT_DESK,
    )

    _, _, membership = (
        create_pending_membership()
    )

    token = login(staff.email)

    client.post(
        "/api/v1/payments/staff",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
            "method": PaymentMethod.CASH.value,
        },
    )

    response = client.get(
        (
            "/api/v1/payments/"
            f"membership/{membership.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1
    assert (
        payments[0]["membership_id"]
        == membership.id
    )





def test_member_can_initialize_online_payment():
    member, plan, membership = (
        create_pending_membership()
    )

    token = login(member.email)

    response = client.post(
        "/api/v1/payments/online/initialize",
        headers=auth_headers(token),
        json={
            "membership_id": membership.id,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert (
        body["payment"]["membership_id"]
        == membership.id
    )
    assert (
        Decimal(body["payment"]["amount"])
        == plan.price
    )
    assert body["payment"]["status"] == "pending"
    assert body["payment"]["method"] == "online"
    assert body["payment"]["paid_at"] is None
    assert body["checkout_url"] is not None