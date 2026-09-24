from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class ReminderKind(StrEnum):
    EXPIRY_7_DAYS = "expiry_7_days"


class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"
    __table_args__ = (
        UniqueConstraint(
            "membership_id",
            "kind",
            name="uq_reminders_membership_id_kind",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    membership_id: int = Field(foreign_key="memberships.id", nullable=False)

    kind: ReminderKind = Field(nullable=False)

    sent_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
