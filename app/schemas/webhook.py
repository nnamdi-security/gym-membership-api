from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentWebhookEvent(BaseModel):
    event_id: str = Field(
        min_length=1,
        max_length=255,
    )

    event_type: str = Field(
        alias="type",
        min_length=1,
        max_length=100,
    )

    reference: str = Field(
        min_length=1,
        max_length=255,
    )

    amount: int = Field(
        gt=0,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    paid_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )