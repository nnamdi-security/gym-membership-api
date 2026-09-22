from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GymClassCreateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )

    capacity: int = Field(
        gt=0,
        le=1000,
    )

    starts_at: datetime

    model_config = ConfigDict(
        extra="forbid",
    )


class GymClassUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
        le=1000,
    )

    starts_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
    )


class GymClassResponse(BaseModel):
    id: int
    name: str
    capacity: int
    starts_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )