from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric, String
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class Plan(SQLModel, table=True):
    __tablename__ = "plans"

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(sa_column=Column(String(120), nullable=False))

    price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    period_days: int = Field(nullable=False, gt=0)

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))