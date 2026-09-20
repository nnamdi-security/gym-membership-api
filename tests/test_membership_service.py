from datetime import date, timedelta

import pytest

from app.models.membership import MembershipStatus
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.membership import MembershipRepository
from app.schemas.membership import MembershipFreezeRequest, MembershipSubscribeRequest
from app.services.membership_service import (
    MembershipNotFoundError,
    MembershipService,
    PlanNotFoundError,
)


@pytest.fixture
def membership_service(db_session):
    return MembershipService(MembershipRepository(db_session), db_session)


@pytest.fixture
def a_plan(db_session):
    plan = Plan(name="Monthly", price=15000, period_days=30)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture
def a_member(db_session):
    user = User(email="member@example.com", password_hash="x", role=UserRole.MEMBER)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_subscribe_creates_pending_membership_with_correct_end_date(
    membership_service, a_plan, a_member
):
    membership = membership_service.subscribe(
        a_member.id, MembershipSubscribeRequest(plan_id=a_plan.id)
    )

    assert membership.status == MembershipStatus.PENDING
    assert membership.start_date == date.today()
    assert membership.end_date == date.today() + timedelta(days=a_plan.period_days)


def test_subscribe_with_invalid_plan_raises_error(membership_service, a_member):
    with pytest.raises(PlanNotFoundError):
        membership_service.subscribe(a_member.id, MembershipSubscribeRequest(plan_id=999999))


def test_freeze_extends_end_date_and_sets_frozen(membership_service, a_plan, a_member):
    membership = membership_service.subscribe(
        a_member.id, MembershipSubscribeRequest(plan_id=a_plan.id)
    )
    original_end_date = membership.end_date

    frozen = membership_service.freeze(membership.id, MembershipFreezeRequest(days=10))

    assert frozen.status == MembershipStatus.FROZEN
    assert frozen.end_date == original_end_date + timedelta(days=10)


def test_unfreeze_sets_status_back_to_active(membership_service, a_plan, a_member):
    membership = membership_service.subscribe(
        a_member.id, MembershipSubscribeRequest(plan_id=a_plan.id)
    )
    membership_service.freeze(membership.id, MembershipFreezeRequest(days=10))

    unfrozen = membership_service.unfreeze(membership.id)

    assert unfrozen.status == MembershipStatus.ACTIVE


def test_freeze_nonexistent_membership_raises_error(membership_service):
    with pytest.raises(MembershipNotFoundError):
        membership_service.freeze(999999, MembershipFreezeRequest(days=10))