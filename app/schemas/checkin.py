from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckinCreateRequest(BaseModel):
    class_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class CheckinForMemberRequest(BaseModel):
    class_id: int = Field(gt=0)
    member_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class CheckinResponse(BaseModel):
    id: int
    class_id: int
    member_id: int
    checked_in_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )