from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.job_run import JobRun
from app.models.membership import MembershipStatus
from app.models.reminder import Reminder, ReminderKind
from app.repositories.job_run_repository import JobRunRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.reminder_repository import ReminderRepository


DAILY_JOB_NAME = "daily_membership_maintenance"


@dataclass
class DailyJobResult:
    status: str
    expired_memberships: int
    reminders_created: int


class DailyJobService:
    def __init__(
        self,
        session: Session,
        job_run_repository: JobRunRepository,
        membership_repository: MembershipRepository,
        reminder_repository: ReminderRepository,
    ):
        self.session = session
        self.job_run_repository = job_run_repository
        self.membership_repository = membership_repository
        self.reminder_repository = reminder_repository

    def run(
        self,
        run_date: date | None = None,
    ) -> DailyJobResult:
        effective_date = run_date or date.today()

        claimed = self._claim_run(
            effective_date
        )

        if not claimed:
            return DailyJobResult(
                status="already_run",
                expired_memberships=0,
                reminders_created=0,
            )

        expired_count = 0
        reminder_count = 0

        try:
            expired_memberships = (
                self.membership_repository.get_active_expired_by(
                    effective_date
                )
            )

            for membership in expired_memberships:
                membership.status = MembershipStatus.EXPIRED

                self.membership_repository.add(
                    membership
                )

                expired_count += 1

            reminder_date = (
                effective_date
                + timedelta(days=7)
            )

            expiring_memberships = (
                self.membership_repository.get_active_expiring_on(
                    reminder_date
                )
            )

            for membership in expiring_memberships:
                existing_reminder = (
                    self.reminder_repository.get_for_membership_and_kind(
                        membership.id,
                        ReminderKind.EXPIRY_7_DAYS,
                    )
                )

                if existing_reminder is not None:
                    continue

                reminder = Reminder(
                    membership_id=membership.id,
                    kind=ReminderKind.EXPIRY_7_DAYS,
                )

                self.reminder_repository.add(
                    reminder
                )

                reminder_count += 1

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return DailyJobResult(
            status="completed",
            expired_memberships=expired_count,
            reminders_created=reminder_count,
        )

    def _claim_run(
        self,
        run_date: date,
    ) -> bool:
        job_run = JobRun(
            job_name=DAILY_JOB_NAME,
            run_date=run_date,
        )

        try:
            self.job_run_repository.add(
                job_run
            )

            self.session.flush()

            return True

        except IntegrityError:
            self.session.rollback()
            return False