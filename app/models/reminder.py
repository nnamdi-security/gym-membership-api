from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel
from app.models.base import utc_now


class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: int | None = Field(default=None, primary_key=True)
    membership_id: int = Field(foreign_key="memberships.id", nullable=False, index=True)
    kind: str = Field(nullable=False)
    sent_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
