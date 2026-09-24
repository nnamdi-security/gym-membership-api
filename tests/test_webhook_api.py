# import hashlib
# import hmac
# import json
# from decimal import Decimal

# from fastapi.testclient import TestClient
# from sqlmodel import Session, select

# from app.core.config import settings
# from app.db.session import engine
# from app.main import app
# from app.models.membership import (
#     Membership,
#     MembershipStatus,
# )
# from app.models.payment import (
#     Payment,
#     PaymentMethod,
#     PaymentStatus,
# )
# from app.models.plan import Plan
# from app.models.processed_event import ProcessedEvent
# from app.models.user import User, UserRole

# client = TestClient(app)


# def sign(
#     raw_body: bytes,
# ) -> str:
#     return hmac.new(
#         settings.webhook_secret.encode(),
#         raw_body,
#         hashlib.sha256,
#     ).hexdigest()


# def create_pending_online_payment():
#     with Session(engine) as session:
#         member = User(
#             email="member@example.com",
#             password_hash="hash",
#             role=UserRole.MEMBER,
#         )

#         plan = Plan(
#             name="Monthly",
#             price=Decimal("15000.00"),
#             period_days=30,
#         )

#         session.add(member)
#         session.add(plan)
#         session.commit()

#         session.refresh(member)
#         session.refresh(plan)

#         membership = Membership(
#             member_id=member.id,
#             plan_id=plan.id,
#             status=MembershipStatus.PENDING_PAYMENT,
#         )

#         session.add(membership)
#         session.commit()
#         session.refresh(membership)

#         payment = Payment(
#             membership_id=membership.id,
#             amount=plan.price,
#             status=PaymentStatus.PENDING,
#             method=PaymentMethod.ONLINE,
#             reference="FITPRO-WEBHOOK-001",
#             provider="mock-provider",
#         )

#         session.add(payment)
#         session.commit()
#         session.refresh(payment)

#         return membership.id, payment.id


# def test_valid_payment_webhook_confirms_once():
#     _, payment_id = create_pending_online_payment()

#     body = {
#         "event_id": "evt_valid_001",
#         "type": "payment.succeeded",
#         "reference": "FITPRO-WEBHOOK-001",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 200
#     assert response.json()["status"] == "processed"

#     with Session(engine) as session:
#         payment = session.get(
#             Payment,
#             payment_id,
#         )

#         membership = session.get(
#             Membership,
#             membership_id,
#         )

#         assert payment is not None
#         assert membership is not None

#         assert payment.status == PaymentStatus.SUCCEEDED

#         assert membership.status == MembershipStatus.ACTIVE


# def test_duplicate_webhook_changes_nothing_twice():
#     membership_id, payment_id = create_pending_online_payment()

#     body = {
#         "event_id": "evt_duplicate_001",
#         "type": "payment.succeeded",
#         "reference": "FITPRO-WEBHOOK-001",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     headers = {
#         "Content-Type": "application/json",
#         "X-Signature": sign(raw_body),
#     }

#     first = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers=headers,
#     )

#     second = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers=headers,
#     )

#     assert first.status_code == 200
#     assert second.status_code == 200

#     assert second.json()["status"] == "duplicate"


# def test_bad_webhook_signature_returns_401():
#     body = {
#         "event_id": "evt_bad_001",
#         "type": "payment.succeeded",
#         "reference": "FITPRO-WEBHOOK-001",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": "deadbeef" * 8,
#         },
#     )

#     assert response.status_code == 401


# def test_orphan_webhook_returns_200():
#     body = {
#         "event_id": "evt_orphan_001",
#         "type": "payment.succeeded",
#         "reference": "REF-DOES-NOT-EXIST",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 200
#     assert response.json()["status"] == "orphan"


# with Session(engine) as session:
#     events = session.exec(
#         select(ProcessedEvent).where(ProcessedEvent.event_id == "evt_duplicate_001")
#     ).all()

#     assert len(events) == 1


# def test_webhook_rejects_wrong_amount():
#     _, _ = create_pending_online_payment()

#     body = {
#         "event_id": "evt_wrong_amount",
#         "type": "payment.succeeded",
#         "reference": "FITPRO-WEBHOOK-001",
#         "amount": 100,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 400
#     assert response.json() == {"detail": "Webhook payment data does not match"}


# def test_webhook_rejects_wrong_currency():
#     create_pending_online_payment()

#     body = {
#         "event_id": "evt_wrong_currency",
#         "type": "payment.succeeded",
#         "reference": "FITPRO-WEBHOOK-001",
#         "amount": 1500000,
#         "currency": "USD",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 400


# with Session(engine) as session:
#     statement = select(ProcessedEvent).where(
#         ProcessedEvent.event_id == "evt_wrong_amount"
#     )

#     event = session.exec(statement).first()

#     assert event is None


# with Session(engine) as session:
#     events = session.exec(
#         select(ProcessedEvent).where(ProcessedEvent.event_id == "evt_valid_001")
#     ).all()

#     assert len(events) == 1


# # with Session(engine) as session:
# #     membership = session.get(
# #         Membership,
# #         membership_id,
# #     )

# #     first_start_date = membership.start_date
# #     first_end_date = membership.end_date


# # with Session(engine) as session:
# #     membership = session.get(
# #         Membership,
# #         membership_id,
# #     )

#     # assert membership.start_date == first_start_date
#     # assert membership.end_date == first_end_date


# def test_unknown_webhook_event_type_is_ignored():
#     body = {
#         "event_id": "evt_other_type",
#         "type": "payment.processing",
#         "reference": "ANYTHING",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 200
#     assert response.json()["status"] == "ignored"


# def test_malformed_webhook_payload_returns_422():
#     raw_body = b'{"event_id":'

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 422


# def test_webhook_missing_reference_returns_422():
#     body = {
#         "event_id": "evt_invalid_payload",
#         "type": "payment.succeeded",
#         "amount": 1500000,
#         "currency": "NGN",
#         "paid_at": "2026-09-22T10:00:00Z",
#     }

#     raw_body = json.dumps(
#         body,
#         separators=(",", ":"),
#     ).encode()

#     response = client.post(
#         "/api/v1/webhooks/payment",
#         content=raw_body,
#         headers={
#             "Content-Type": "application/json",
#             "X-Signature": sign(raw_body),
#         },
#     )

#     assert response.status_code == 422
