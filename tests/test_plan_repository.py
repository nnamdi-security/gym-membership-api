from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlmodel import Session

from app.db.session import engine
from app.models.membership import Membership, MembershipStatus
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.plan_repository import PlanRepository


def test_create_plan():

    with Session(engine) as session:
        repository = PlanRepository(session)

        plan = Plan(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )

        created = repository.create(plan)

        assert created.id is not None
        assert created.name == "Monthly"
        assert created.price == Decimal("15000.00")
        assert created.period_days == 30


def test_get_plan_by_id():

    with Session(engine) as session:
        repository = PlanRepository(session)

        created = repository.create(
            Plan(
                name="Quarterly",
                price=Decimal("40000.00"),
                period_days=90,
            )
        )

        found = repository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "Quarterly"


def test_get_by_id_returns_none_for_missing_plan():

    with Session(engine) as session:
        repository = PlanRepository(session)

        found = repository.get_by_id(999999)

        assert found is None


def test_get_all_plans():

    with Session(engine) as session:
        repository = PlanRepository(session)

        repository.create(
            Plan(
                name="Monthly",
                price=Decimal("15000.00"),
                period_days=30,
            )
        )

        repository.create(
            Plan(
                name="Quarterly",
                price=Decimal("40000.00"),
                period_days=90,
            )
        )

        plans = repository.get_all()

        assert len(plans) == 2
        assert plans[0].name == "Monthly"
        assert plans[1].name == "Quarterly"


def test_update_plan():

    with Session(engine) as session:
        repository = PlanRepository(session)

        plan = repository.create(
            Plan(
                name="Monthly",
                price=Decimal("15000.00"),
                period_days=30,
            )
        )

        plan.price = Decimal("17000.00")

        updated = repository.update(plan)

        assert updated.price == Decimal("17000.00")


def test_delete_plan():

    with Session(engine) as session:
        repository = PlanRepository(session)

        plan = repository.create(
            Plan(
                name="Temporary",
                price=Decimal("5000.00"),
                period_days=7,
            )
        )

        plan_id = plan.id

        repository.delete(plan)

        found = repository.get_by_id(plan_id)

        assert found is None


def test_has_memberships_returns_true_for_used_plan(
    db_session,
):
    repository = PlanRepository(db_session)

    member = User(
        email="member@example.com",
        password_hash="hashed-password",
        role=UserRole.MEMBER,
    )
    db_session.add(member)

    plan = Plan(
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )
    db_session.add(plan)

    db_session.commit()
    db_session.refresh(member)
    db_session.refresh(plan)

    membership = Membership(
        member_id=member.id,
        plan_id=plan.id,
        start_date=datetime.now(timezone.utc).date(),
        end_date=datetime.now(timezone.utc).date() + timedelta(days=30),
        status=MembershipStatus.ACTIVE,
    )

    db_session.add(membership)
    db_session.commit()

    assert repository.has_memberships(plan.id) is True


def test_has_memberships_returns_false_for_unused_plan(
    db_session,
):
    repository = PlanRepository(db_session)

    plan = repository.create(
        Plan(
            name="Unused",
            price=Decimal("5000.00"),
            period_days=7,
        )
    )

    assert repository.has_memberships(plan.id) is False
