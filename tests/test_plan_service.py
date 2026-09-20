from decimal import Decimal

import pytest

from app.models.plan import Plan
from app.schemas.plan import (
    PlanCreateRequest,
    PlanUpdateRequest,
)
from app.services.plan_service import (
    PlanInUseError,
    PlanNotFoundError,
    PlanService,
)


# fake repository
class FakePlanRepository:
    def __init__(self):
        self.plans: dict[int, Plan] = {}
        self.next_id = 1
        self.used_plan_ids: set[int] = set()

    def get_all(self) -> list[Plan]:
        return list(self.plans.values())

    def get_by_id(self, plan_id: int) -> Plan | None:
        return self.plans.get(plan_id)

    def create(self, plan: Plan) -> Plan:
        plan.id = self.next_id
        self.next_id += 1
        self.plans[plan.id] = plan

        return plan

    def update(self, plan: Plan) -> Plan:
        self.plans[plan.id] = plan
        return plan

    def delete(self, plan: Plan) -> None:
        del self.plans[plan.id]

    def has_memberships(self, plan_id: int) -> bool:
        return plan_id in self.used_plan_ids


# PALN CREATION
def test_create_plan():
    repository = FakePlanRepository()
    service = PlanService(repository)

    plan = service.create_plan(
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )
    )

    assert plan.id == 1
    assert plan.name == "Monthly"
    assert plan.price == Decimal("15000.00")
    assert plan.period_days == 30


# TEST LISTING
def test_list_plans():
    repository = FakePlanRepository()
    service = PlanService(repository)

    service.create_plan(
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )
    )

    service.create_plan(
        PlanCreateRequest(
            name="Quarterly",
            price=Decimal("40000.00"),
            period_days=90,
        )
    )

    plans = service.list_plans()

    assert len(plans) == 2


def test_get_plan_raises_when_missing():
    repository = FakePlanRepository()
    service = PlanService(repository)

    with pytest.raises(PlanNotFoundError):
        service.get_plan(999)


def test_update_plan_changes_only_supplied_fields():
    repository = FakePlanRepository()
    service = PlanService(repository)

    original = service.create_plan(
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=30,
        )
    )

    updated = service.update_plan(
        original.id,
        PlanUpdateRequest(
            price=Decimal("17000.00"),
        ),
    )

    assert updated.name == "Monthly"
    assert updated.price == Decimal("17000.00")
    assert updated.period_days == 30


def test_delete_unused_plan():
    repository = FakePlanRepository()
    service = PlanService(repository)

    plan = service.create_plan(
        PlanCreateRequest(
            name="Temporary",
            price=Decimal("5000.00"),
            period_days=7,
        )
    )

    service.delete_plan(plan.id)

    assert repository.get_by_id(plan.id) is None


def test_delete_plan_rejects_plan_with_memberships():
    repository = FakePlanRepository()
    service = PlanService(repository)

    plan = service.create_plan(
        PlanCreateRequest(
            name="Annual",
            price=Decimal("140000.00"),
            period_days=365,
        )
    )

    repository.used_plan_ids.add(plan.id)

    with pytest.raises(PlanInUseError):
        service.delete_plan(plan.id)

    assert repository.get_by_id(plan.id) is not None
