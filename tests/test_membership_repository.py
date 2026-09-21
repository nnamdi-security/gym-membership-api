from decimal import Decimal

from app.models.membership import Membership, MembershipStatus
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.membership_repository import MembershipRepository


def create_member_and_plan(db_session):
    member = User(
        email="member@example.com",
        password_hash="hashed-password",
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

    return member, plan


def test_create_pending_membership(db_session):
    member, plan = create_member_and_plan(db_session)

    repository = MembershipRepository(db_session)

    membership = Membership(
        member_id=member.id,
        plan_id=plan.id,
        status=MembershipStatus.PENDING_PAYMENT,
    )

    created = repository.create(membership)

    assert created.id is not None
    assert created.member_id == member.id
    assert created.plan_id == plan.id
    assert created.status == MembershipStatus.PENDING_PAYMENT
    assert created.start_date is None
    assert created.end_date is None


def test_get_for_member_returns_membership_history(db_session):
    member, plan = create_member_and_plan(db_session)

    repository = MembershipRepository(db_session)

    first = repository.create(
        Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.EXPIRED,
        )
    )

    second = repository.create(
        Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.PENDING_PAYMENT,
        )
    )

    memberships = repository.get_for_member(member.id)

    assert len(memberships) == 2
    assert memberships[0].id == second.id
    assert memberships[1].id == first.id


def test_get_active_for_member_returns_active_membership(db_session):
    member, plan = create_member_and_plan(db_session)

    repository = MembershipRepository(db_session)

    repository.create(
        Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.EXPIRED,
        )
    )

    active = repository.create(
        Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
        )
    )

    found = repository.get_active_for_member(member.id)

    assert found is not None
    assert found.id == active.id


def test_get_active_for_member_returns_none_when_missing(
    db_session,
):
    member, _ = create_member_and_plan(db_session)

    repository = MembershipRepository(db_session)

    assert repository.get_active_for_member(member.id) is None


def test_get_pending_for_member_returns_pending_membership(
    db_session,
):
    member, plan = create_member_and_plan(db_session)

    repository = MembershipRepository(db_session)

    pending = repository.create(
        Membership(
            member_id=member.id,
            plan_id=plan.id,
            status=MembershipStatus.PENDING_PAYMENT,
        )
    )

    found = repository.get_pending_for_member(member.id)

    assert found is not None
    assert found.id == pending.id
