from decimal import Decimal

from sqlmodel import Session, delete

from app.db.session import engine
from app.models.plan import Plan
from app.repositories.plan_repository import PlanRepository


def clear_plans():
    with Session(engine) as session:
        session.exec(delete(Plan))
        session.commit()


def test_create_plan():
    clear_plans()

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
    clear_plans()

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
    clear_plans()

    with Session(engine) as session:
        repository = PlanRepository(session)

        found = repository.get_by_id(999999)

        assert found is None





def test_get_all_plans():
    clear_plans()

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
    clear_plans()

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
    clear_plans()

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