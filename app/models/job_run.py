from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class JobRun(SQLModel, table=True):
    __tablename__ = "job_runs"
    __table_args__ = (
        UniqueConstraint(
            "job_name",
            "run_date",
            name="uq_job_runs_job_name_run_date",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    job_name: str = Field(sa_column=Column(String(100), nullable=False))

    run_date: date = Field(sa_column=Column(Date, nullable=False))

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
