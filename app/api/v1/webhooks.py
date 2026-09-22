import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_database
from app.models.processed_event import ProcessedEvent

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/payment", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    session: Session = Depends(get_database),
):
    body = await request.body()
    signature = request.headers.get("X-Signature", "")

    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    payload = await request.json()
    event_id = payload.get("event_id")
    reference = payload.get("reference")

    event = ProcessedEvent(event_id=event_id, reference=reference)
    session.add(event)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return {"status": "already processed"}

    # TODO: look up the reference and confirm the payment once PaymentService exists

    return {"status": "received"}