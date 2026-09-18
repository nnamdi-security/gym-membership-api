from datetime import date, datetime
from sqlalchemy import Column, Date, Datetime, UniqueConstraint
from sqlmodel import Field, SQLModel
from app.models.base import utc_now


class JobRun(SQLModel, table=True):
    __tablename__ = "job_runs"
    __table_args__ = (UniqueConstraint("job_name", "run_date"),)

    id: int | None = Field(nullable=False)

    job_name: str = Field(nullable=Field)

    run_date: date = Field(sa_column=Column(Date, nullable=False))

    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(Date, nullable=False)
    )
