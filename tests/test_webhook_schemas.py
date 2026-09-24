from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.webhook import PaymentWebhookEvent


def test_payment_webhook_event_accepts_provider_payload():
    event = PaymentWebhookEvent(
        event_id="evt_abc123",
        type="payment.succeeded",
        reference="FITPRO-ABC",
        amount=1500000,
        currency="NGN",
        paid_at=datetime.now(UTC),
    )

    assert event.event_id == "evt_abc123"
    assert event.event_type == "payment.succeeded"
    assert event.amount == 1500000


def test_payment_webhook_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        PaymentWebhookEvent(
            event_id="evt_abc123",
            type="payment.succeeded",
            reference="FITPRO-ABC",
            amount=0,
            currency="NGN",
            paid_at=datetime.now(UTC),
        )
