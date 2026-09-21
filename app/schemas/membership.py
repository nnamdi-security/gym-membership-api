from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.membership import MembershipStatus


class MembershipSubscribeRequest(BaseModel):
    plan_id: int


class MembershipFreezeRequest(BaseModel):
    days: int = Field(gt=0, le=365)


class MembershipResponse(BaseModel):
    id: int
    member_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: MembershipStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
