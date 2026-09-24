from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import (
    PaymentMethod,
    PaymentStatus,
)


class StaffPaymentRequest(BaseModel):
    membership_id: int = Field(gt=0)

    method: PaymentMethod

    model_config = ConfigDict(
        extra="forbid",
    )


class PaymentResponse(BaseModel):
    id: int
    membership_id: int
    amount: Decimal
    status: PaymentStatus
    method: PaymentMethod
    reference: str
    provider: str | None
    recorded_by: int | None
    recorded_at: datetime
    paid_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class OnlinePaymentInitializeRequest(BaseModel):
    membership_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class OnlinePaymentInitializeResponse(BaseModel):
    payment: PaymentResponse
    checkout_url: str | None
