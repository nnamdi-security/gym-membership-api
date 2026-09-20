from sqlmodel import Session, select
from app.models.membership import Membership

from app.models.plan import Plan


class PlanRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Plan]:
        statement = select(Plan).order_by(Plan.id)

        return list(self.session.exec(statement).all())

    def get_by_id(self, plan_id: int) -> Plan | None:
        return self.session.get(Plan, plan_id)

    def create(self, plan: Plan) -> Plan:
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)

        return plan
    

    def update(self, plan: Plan) -> Plan:
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)

        return plan
    
    #delete() take a plan as a parameter because the service will already fetch the plan to verify it exists and check business rules. That prevents an unnecessary second lookup.
    def delete(self, plan: Plan) -> None:
        self.session.delete(plan)
        self.session.commit()


    def has_memberships(self, plan_id: int) -> bool:
        statement = (
            select(Membership.id)
            .where(Membership.plan_id == plan_id)
            .limit(1)
        )

        return self.session.exec(statement).first() is not None