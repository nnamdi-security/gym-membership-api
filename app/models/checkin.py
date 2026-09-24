from datetime import datetime

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class Checkin(SQLModel, table=True):
    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "member_id",
            name="uq_checkins_class_id_member_id",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    class_id: int = Field(foreign_key="classes.id", nullable=False)

    member_id: int = Field(foreign_key="users.id", nullable=False)

    checked_in_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
