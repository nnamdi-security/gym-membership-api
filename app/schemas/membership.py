from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.membership import MembershipStatus


class MembershipCreateRequest(BaseModel):
    plan_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class MembershipCreateForMemberRequest(BaseModel):
    member_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class MembershipResponse(BaseModel):
    id: int
    member_id: int
    plan_id: int

    start_date: date | None
    end_date: date | None
    frozen_on: date | None

    status: MembershipStatus

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )