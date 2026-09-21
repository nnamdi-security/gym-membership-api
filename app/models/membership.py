from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Column, Date, DateTime, Index
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class MembershipStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    FROZEN = "frozen"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Membership(SQLModel, table=True):
    __tablename__ = "memberships"
    __table_args__ = (
        Index(
            "ix_memberships_end_date_status",
            "end_date",
            "status",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    member_id: int = Field(foreign_key="users.id", nullable=False)

    plan_id: int = Field(foreign_key="plans.id", nullable=False)

    start_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))

    end_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))

    status: MembershipStatus = Field(default=MembershipStatus.PENDING_PAYMENT, nullable=False)

    frozen_on: date | None = Field(default=None, sa_column=Column(Date, nullable=True))

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

  