from datetime import datetime, timezone

from app.models.plan import Plan
from app.repositories.plan_repository import PlanRepository
from app.schemas.plan import (
    PlanCreateRequest,
    PlanUpdateRequest,
)


class PlanNotFoundError(Exception):
    pass


class PlanInUseError(Exception):
    pass


class PlanService:
    def __init__(self, plan_repository: PlanRepository):
        self.plan_repository = plan_repository

    def list_plans(self) -> list[Plan]:
        return self.plan_repository.get_all()

    def get_plan(self, plan_id: int) -> Plan:
        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None:
            raise PlanNotFoundError

        return plan

    def create_plan(self, data: PlanCreateRequest) -> Plan:
        plan = Plan(
            name=data.name,
            price=data.price,
            period_days=data.period_days,
        )

        return self.plan_repository.create(plan)

    def update_plan(self, plan_id: int, data: PlanUpdateRequest) -> Plan:
        plan = self.get_plan(plan_id)

        updates = data.model_dump(
            exclude_unset=True,
        )

        for field, value in updates.items():
            setattr(plan, field, value)

        plan.updated_at = datetime.now(timezone.utc)

        return self.plan_repository.update(plan)

    def delete_plan(self, plan_id: int) -> None:
        plan = self.get_plan(plan_id)

        if self.plan_repository.has_memberships(plan_id):
            raise PlanInUseError

        self.plan_repository.delete(plan)
