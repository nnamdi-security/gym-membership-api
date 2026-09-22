import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlmodel import Session

from app.core.webhook_security import (
    verify_webhook_signature,
)
from app.db.session import get_session
from app.repositories.membership_repository import MembershipRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.processed_event_repository import (
    ProcessedEventRepository,
)
from app.schemas.webhook import PaymentWebhookEvent
from app.services.webhook_service import (
    WebhookPaymentMismatchError,
    WebhookService,
)


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


SESSION_DEPENDENCY = Depends(get_session)


def get_webhook_service(
    session: Session = SESSION_DEPENDENCY,
) -> WebhookService:
    return WebhookService(
        session=session,
        payment_repository=PaymentRepository(
            session
        ),
        membership_repository=MembershipRepository(
            session
        ),
        plan_repository=PlanRepository(
            session
        ),
        processed_event_repository=ProcessedEventRepository(
            session
        ),
    )


WEBHOOK_SERVICE_DEPENDENCY = Depends(
    get_webhook_service
)



# Endpoint
@router.post(
    "/payment",
    status_code=status.HTTP_200_OK,
    summary="Receive payment provider webhook",
)
async def payment_webhook(
    request: Request,
    service: WebhookService = WEBHOOK_SERVICE_DEPENDENCY,
):
    raw_body = await request.body()

    signature = request.headers.get(
        "X-Signature"
    )

    if (
        signature is None
        or not verify_webhook_signature(
            raw_body,
            signature,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        payload = json.loads(raw_body)

        event = PaymentWebhookEvent.model_validate(
            payload
        )

    except (
        json.JSONDecodeError,
        ValidationError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid webhook payload",
        ) from None

    try:
        result = service.process_payment_event(
            event
        )

    except WebhookPaymentMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payment data does not match",
        ) from None

    return {
        "status": result.status,
    }