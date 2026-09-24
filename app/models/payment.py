from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Column, DateTime, Numeric, String
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentMethod(StrEnum):
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"
    ONLINE = "online"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    membership_id: int = Field(
        foreign_key="memberships.id",
        nullable=False,
    )

    amount: Decimal = Field(
        sa_column=Column(
            Numeric(12, 2),
            nullable=False,
        )
    )

    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    method: PaymentMethod = Field(
        nullable=False,
    )

    reference: str = Field(
        sa_column=Column(
            String(255),
            nullable=False,
            unique=True,
            index=True,
        )
    )

    provider: str | None = Field(
        default=None,
        sa_column=Column(
            String(100),
            nullable=True,
        ),
    )

    recorded_by: int | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
    )

    recorded_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
    )

    paid_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
        ),
    )
