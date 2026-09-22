import hashlib
import hmac
import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.plan import Plan
from app.models.user import User, UserRole


from sqlmodel import select

from app.models.processed_event import ProcessedEvent


client = TestClient(app)


def sign(
    raw_body: bytes,
) -> str:
    return hmac.new(
        settings.webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()




def create_pending_online_payment():
    with Session(engine) as session:
        member = User(
            email="member@example.com",
            password_hash="hash",
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

        payment = Payment(
            membership_id=membership.id,
            amount=plan.price,
            status=PaymentStatus.PENDING,
            method=PaymentMethod.ONLINE,
            reference="FITPRO-WEBHOOK-001",
            provider="mock-provider",
        )

        session.add(payment)
        session.commit()
        session.refresh(payment)

        return membership.id, payment.id




def test_valid_payment_webhook_confirms_once():
    membership_id, payment_id = (
        create_pending_online_payment()
    )

    body = {
        "event_id": "evt_valid_001",
        "type": "payment.succeeded",
        "reference": "FITPRO-WEBHOOK-001",
        "amount": 1500000,
        "currency": "NGN",
        "paid_at": "2026-09-22T10:00:00Z",
    }

    raw_body = json.dumps(
        body,
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sign(raw_body),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    with Session(engine) as session:
        payment = session.get(
            Payment,
            payment_id,
        )

        membership = session.get(
            Membership,
            membership_id,
        )

        assert payment is not None
        assert membership is not None

        assert (
            payment.status
            == PaymentStatus.SUCCEEDED
        )

        assert (
            membership.status
            == MembershipStatus.ACTIVE
        )



def test_duplicate_webhook_changes_nothing_twice():
    membership_id, payment_id = (
        create_pending_online_payment()
    )

    body = {
        "event_id": "evt_duplicate_001",
        "type": "payment.succeeded",
        "reference": "FITPRO-WEBHOOK-001",
        "amount": 1500000,
        "currency": "NGN",
        "paid_at": "2026-09-22T10:00:00Z",
    }

    raw_body = json.dumps(
        body,
        separators=(",", ":"),
    ).encode()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sign(raw_body),
    }

    first = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers=headers,
    )

    second = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["status"] == "duplicate"





def test_bad_webhook_signature_returns_401():
    body = {
        "event_id": "evt_bad_001",
        "type": "payment.succeeded",
        "reference": "FITPRO-WEBHOOK-001",
        "amount": 1500000,
        "currency": "NGN",
        "paid_at": "2026-09-22T10:00:00Z",
    }

    raw_body = json.dumps(
        body,
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "deadbeef" * 8,
        },
    )

    assert response.status_code == 401




def test_orphan_webhook_returns_200():
    body = {
        "event_id": "evt_orphan_001",
        "type": "payment.succeeded",
        "reference": "REF-DOES-NOT-EXIST",
        "amount": 1500000,
        "currency": "NGN",
        "paid_at": "2026-09-22T10:00:00Z",
    }

    raw_body = json.dumps(
        body,
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sign(raw_body),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "orphan"



with Session(engine) as session:
    events = session.exec(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id
            == "evt_duplicate_001"
        )
    ).all()

    assert len(events) == 1