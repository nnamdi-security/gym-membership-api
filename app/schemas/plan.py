from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PlanCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)

    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    period_days: int = Field(gt=0, le=3650)


class PlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)

    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    period_days: int | None = Field(default=None, gt=0, le=3650)


class PlanResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    period_days: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
