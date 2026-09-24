from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.plan import Plan
from app.models.reminder import (
    Reminder,
    ReminderKind,
)
from app.models.user import User, UserRole
from app.repositories.reminder_repository import (
    ReminderRepository,
)


def create_membership(
    db_session,
) -> Membership:
    member = User(
        email="member@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    plan = Plan(
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )

    db_session.add(member)
    db_session.add(plan)
    db_session.commit()

    db_session.refresh(member)
    db_session.refresh(plan)

    today = datetime.now(tz=timezone.utc).date()

    membership = Membership(
        member_id=member.id,
        plan_id=plan.id,
        status=MembershipStatus.ACTIVE,
        start_date=today,
        end_date=today + timedelta(days=30),
    )

    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)

    return membership


def test_create_reminder(
    db_session,
):
    membership = create_membership(db_session)

    repository = ReminderRepository(db_session)

    reminder = repository.create(
        Reminder(
            membership_id=membership.id,
            kind=ReminderKind.EXPIRY_7_DAYS,
        )
    )

    assert reminder.id is not None
    assert reminder.membership_id == membership.id


def test_get_reminder_for_membership_and_kind(
    db_session,
):
    membership = create_membership(db_session)

    repository = ReminderRepository(db_session)

    created = repository.create(
        Reminder(
            membership_id=membership.id,
            kind=ReminderKind.EXPIRY_7_DAYS,
        )
    )

    found = repository.get_for_membership_and_kind(
        membership.id,
        ReminderKind.EXPIRY_7_DAYS,
    )

    assert found is not None
    assert found.id == created.id


def test_duplicate_reminder_is_rejected(
    db_session,
):
    membership = create_membership(db_session)

    repository = ReminderRepository(db_session)

    repository.create(
        Reminder(
            membership_id=membership.id,
            kind=ReminderKind.EXPIRY_7_DAYS,
        )
    )

    duplicate = Reminder(
        membership_id=membership.id,
        kind=ReminderKind.EXPIRY_7_DAYS,
    )

    with pytest.raises(IntegrityError):
        repository.create(duplicate)

    db_session.rollback()
