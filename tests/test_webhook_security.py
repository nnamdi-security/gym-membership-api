import hashlib
import hmac

from app.core.config import settings
from app.core.webhook_security import (
    verify_webhook_signature,
)


def sign(
    raw_body: bytes,
) -> str:
    return hmac.new(
        settings.webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def test_valid_webhook_signature_is_accepted():
    raw_body = (
        b'{"event_id":"evt_1",'
        b'"type":"payment.succeeded"}'
    )

    signature = sign(raw_body)

    assert verify_webhook_signature(
        raw_body,
        signature,
    )


def test_invalid_webhook_signature_is_rejected():
    raw_body = (
        b'{"event_id":"evt_1",'
        b'"type":"payment.succeeded"}'
    )

    assert not verify_webhook_signature(
        raw_body,
        "deadbeef" * 8,
    )