from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class ProcessedEvent(SQLModel, table=True):
    __tablename__ = "processed_events"

    id: int | None = Field(default=None, primary_key=True)

    event_id: str = Field(sa_column=Column(String(255), nullable=False, unique=True, index=True))

    reference: str = Field(sa_column=Column(String(255), nullable=False))

    processed_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))