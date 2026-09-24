from datetime import date

from sqlmodel import Session, select

from app.models.job_run import JobRun


class JobRunRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_by_job_and_date(
        self,
        job_name: str,
        run_date: date,
    ) -> JobRun | None:
        statement = select(JobRun).where(
            JobRun.job_name == job_name,
            JobRun.run_date == run_date,
        )

        return self.session.exec(statement).first()

    def add(
        self,
        job_run: JobRun,
    ) -> JobRun:
        self.session.add(job_run)

        return job_run

    def create(
        self,
        job_run: JobRun,
    ) -> JobRun:
        self.session.add(job_run)
        self.session.commit()
        self.session.refresh(job_run)

        return job_run
