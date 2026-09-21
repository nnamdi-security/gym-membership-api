from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class GymClass(SQLModel, table=True):
    __tablename__ = "classes"
    __table_args__ = (
        Index(
            "ix_classes_starts_at",
            "starts_at",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(sa_column=Column(String(120), nullable=False))

    capacity: int = Field(nullable=False, gt=0)

    starts_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
