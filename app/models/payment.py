from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: int | None = Field(default=None, primary_key=True)

    membership_id: int = Field(foreign_key="memberships.id", nullable=False)

    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    recorded_by: int = Field(foreign_key="users.id", nullable=False)

    recorded_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))