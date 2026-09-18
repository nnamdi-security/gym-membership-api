from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel
from app.models.base import utc_now


class ProcessedEvent(SQLModel, table=True):
    __tablename__ = "processed_events"

    id: int | None = Field(default=None, primary_key=True)

    event_id: str = Field(nullable=False)

    reference: str = Field(nullable=False)

    Processed_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
