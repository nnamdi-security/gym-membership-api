from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from threading import Barrier

from sqlmodel import Session, func, select

from app.db.session import engine
from app.models.job_run import JobRun
from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.plan import Plan
from app.models.reminder import Reminder, ReminderKind
from app.models.user import User, UserRole
from app.repositories.job_run_repository import JobRunRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.daily_job_service import (
    DAILY_JOB_NAME,
    DailyJobService,
)


TEST_RUN_DATE = date(2026, 9, 23)




def prepare_daily_job_data() -> tuple[int, int]:
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        expiring_member = User(
            email="expiring@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        reminder_member = User(
            email="reminder@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(expiring_member)
        session.add(reminder_member)
        session.commit()

        session.refresh(plan)
        session.refresh(expiring_member)
        session.refresh(reminder_member)

        expired_due = Membership(
            member_id=expiring_member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=30),
            end_date=TEST_RUN_DATE,
        )

        reminder_due = Membership(
            member_id=reminder_member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=23),
            end_date=TEST_RUN_DATE + timedelta(days=7),
        )

        session.add(expired_due)
        session.add(reminder_due)
        session.commit()

        session.refresh(expired_due)
        session.refresh(reminder_due)

        return (
            expired_due.id,
            reminder_due.id,
        )




def build_daily_job_service(
    session: Session,
) -> DailyJobService:
    return DailyJobService(
        session=session,
        job_run_repository=JobRunRepository(session),
        membership_repository=MembershipRepository(session),
        reminder_repository=ReminderRepository(session),
    )




def test_daily_job_is_safe_to_run_twice():
    expired_id, reminder_id = prepare_daily_job_data()

    with Session(engine) as session:
        service = build_daily_job_service(session)

        first = service.run(
            TEST_RUN_DATE
        )

    with Session(engine) as session:
        service = build_daily_job_service(session)

        second = service.run(
            TEST_RUN_DATE
        )

    assert first.status == "completed"
    assert first.expired_memberships == 1
    assert first.reminders_created == 1

    assert second.status == "already_run"
    assert second.expired_memberships == 0
    assert second.reminders_created == 0

    with Session(engine) as session:
        expired_membership = session.get(
            Membership,
            expired_id,
        )

        reminder_membership = session.get(
            Membership,
            reminder_id,
        )

        assert expired_membership is not None
        assert reminder_membership is not None

        assert (
            expired_membership.status
            == MembershipStatus.EXPIRED
        )

        assert (
            reminder_membership.status
            == MembershipStatus.ACTIVE
        )



with Session(engine) as session:
    job_runs = session.exec(
        select(JobRun).where(
            JobRun.job_name == DAILY_JOB_NAME,
            JobRun.run_date == TEST_RUN_DATE,
        )
    ).all()

    assert len(job_runs) == 1



with Session(engine) as session:
    reminders = session.exec(
        select(Reminder).where(
            Reminder.membership_id == reminder_id,
            Reminder.kind == ReminderKind.EXPIRY_7_DAYS,
        )
    ).all()

    assert len(reminders) == 1




def attempt_daily_job(
    barrier: Barrier,
) -> str:
    with Session(engine) as session:
        service = build_daily_job_service(
            session
        )

        barrier.wait()

        result = service.run(
            TEST_RUN_DATE
        )

        return result.status



def test_two_concurrent_daily_runs_execute_business_work_once():
    expired_id, reminder_id = prepare_daily_job_data()

    barrier = Barrier(2)

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:
        first_future = executor.submit(
            attempt_daily_job,
            barrier,
        )

        second_future = executor.submit(
            attempt_daily_job,
            barrier,
        )

        results = [
            first_future.result(),
            second_future.result(),
        ]

    assert sorted(results) == [
        "already_run",
        "completed",
    ]





    with Session(engine) as session:
        expired_membership = session.get(
            Membership,
            expired_id,
        )

        assert expired_membership is not None
        assert (
            expired_membership.status
            == MembershipStatus.EXPIRED
        )

        reminders = session.exec(
            select(Reminder).where(
                Reminder.membership_id == reminder_id,
                Reminder.kind == ReminderKind.EXPIRY_7_DAYS,
            )
        ).all()

        assert len(reminders) == 1

        job_runs = session.exec(
            select(JobRun).where(
                JobRun.job_name == DAILY_JOB_NAME,
                JobRun.run_date == TEST_RUN_DATE,
            )
        ).all()

        assert len(job_runs) == 1









class FailingReminderRepository(ReminderRepository):
    def add(
        self,
        reminder: Reminder,
    ) -> Reminder:
        raise RuntimeError(
            "simulated reminder failure"
        )


    




import pytest


def test_failed_daily_job_rolls_back_run_claim():
    _, _ = prepare_daily_job_data()

    with Session(engine) as session:
        service = DailyJobService(
            session=session,
            job_run_repository=JobRunRepository(
                session
            ),
            membership_repository=MembershipRepository(
                session
            ),
            reminder_repository=FailingReminderRepository(
                session
            ),
        )

        with pytest.raises(RuntimeError):
            service.run(
                TEST_RUN_DATE
            )

    with Session(engine) as session:
        job_run = session.exec(
            select(JobRun).where(
                JobRun.job_name == DAILY_JOB_NAME,
                JobRun.run_date == TEST_RUN_DATE,
            )
        ).first()

        assert job_run is None




def test_failed_daily_job_rolls_back_all_changes():
    expired_id, _ = prepare_daily_job_data()

    with Session(engine) as session:
        service = DailyJobService(
            session=session,
            job_run_repository=JobRunRepository(
                session
            ),
            membership_repository=MembershipRepository(
                session
            ),
            reminder_repository=FailingReminderRepository(
                session
            ),
        )

        with pytest.raises(RuntimeError):
            service.run(
                TEST_RUN_DATE
            )

    with Session(engine) as session:
        membership = session.get(
            Membership,
            expired_id,
        )

        assert membership is not None

        assert (
            membership.status
            == MembershipStatus.ACTIVE
        )




def test_daily_job_does_not_expire_frozen_membership():
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        member = User(
            email="frozen@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(member)
        session.commit()

        session.refresh(plan)
        session.refresh(member)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.FROZEN,
            start_date=TEST_RUN_DATE - timedelta(days=30),
            end_date=TEST_RUN_DATE,
            frozen_on=TEST_RUN_DATE - timedelta(days=5),
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        membership_id = membership.id

    with Session(engine) as session:
        service = build_daily_job_service(session)

        result = service.run(TEST_RUN_DATE)

    assert result.status == "completed"
    assert result.expired_memberships == 0

    with Session(engine) as session:
        membership = session.get(
            Membership,
            membership_id,
        )

        assert membership is not None
        assert membership.status == MembershipStatus.FROZEN




def test_daily_job_expires_membership_missed_on_previous_day():
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        member = User(
            email="overdue@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(member)
        session.commit()

        session.refresh(plan)
        session.refresh(member)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=31),
            end_date=TEST_RUN_DATE - timedelta(days=1),
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        membership_id = membership.id

    with Session(engine) as session:
        service = build_daily_job_service(session)

        result = service.run(TEST_RUN_DATE)

    assert result.expired_memberships == 1

    with Session(engine) as session:
        membership = session.get(
            Membership,
            membership_id,
        )

        assert membership is not None
        assert membership.status == MembershipStatus.EXPIRED





def test_daily_job_creates_reminder_exactly_seven_days_before_expiry():
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        member = User(
            email="seven-days@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(member)
        session.commit()

        session.refresh(plan)
        session.refresh(member)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=23),
            end_date=TEST_RUN_DATE + timedelta(days=7),
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        membership_id = membership.id

    with Session(engine) as session:
        service = build_daily_job_service(session)

        result = service.run(TEST_RUN_DATE)

    assert result.reminders_created == 1

    with Session(engine) as session:
        reminders = session.exec(
            select(Reminder).where(
                Reminder.membership_id == membership_id,
                Reminder.kind == ReminderKind.EXPIRY_7_DAYS,
            )
        ).all()

        assert len(reminders) == 1




def test_daily_job_does_not_create_reminder_six_days_before_expiry():
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        member = User(
            email="six-days@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(member)
        session.commit()

        session.refresh(plan)
        session.refresh(member)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=24),
            end_date=TEST_RUN_DATE + timedelta(days=6),
        )

        session.add(membership)
        session.commit()

    with Session(engine) as session:
        service = build_daily_job_service(session)

        result = service.run(TEST_RUN_DATE)

    assert result.reminders_created == 0





def test_existing_expiry_reminder_is_not_duplicated():
    with Session(engine) as session:
        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        member = User(
            email="existing-reminder@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(plan)
        session.add(member)
        session.commit()

        session.refresh(plan)
        session.refresh(member)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=TEST_RUN_DATE - timedelta(days=23),
            end_date=TEST_RUN_DATE + timedelta(days=7),
        )

        session.add(membership)
        session.commit()
        session.refresh(membership)

        reminder = Reminder(
            membership_id=membership.id,
            kind=ReminderKind.EXPIRY_7_DAYS,
        )

        session.add(reminder)
        session.commit()

        membership_id = membership.id

    with Session(engine) as session:
        service = build_daily_job_service(session)

        result = service.run(TEST_RUN_DATE)

    assert result.reminders_created == 0

    with Session(engine) as session:
        reminders = session.exec(
            select(Reminder).where(
                Reminder.membership_id == membership_id,
                Reminder.kind == ReminderKind.EXPIRY_7_DAYS,
            )
        ).all()

        assert len(reminders) == 1