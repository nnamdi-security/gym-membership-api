import hashlib
import hmac

from app.core.config import settings


def verify_webhook_signature(
    raw_body: bytes,
    signature: str,
) -> bool:
    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


# hmac.compare_digest(...) is specifically intended for comparing cryptographic values and avoids timing differences associated with ordinary string comparison.
