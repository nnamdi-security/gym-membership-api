from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.models.membership import Membership, MembershipStatus
from app.models.plan import Plan
from app.repositories.membership import MembershipRepository
from app.schemas.membership import MembershipFreezeRequest, MembershipSubscribeRequest


class PlanNotFoundError(Exception):
    pass


class MembershipNotFoundError(Exception):
    pass


class MembershipService:
    def __init__(self, membership_repository: MembershipRepository, session: Session):
        self.membership_repository = membership_repository
        self.session = session

    def subscribe(self, member_id: int, data: MembershipSubscribeRequest) -> Membership:
        plan = self.session.get(Plan, data.plan_id)
        if plan is None:
            raise PlanNotFoundError

        start_date = datetime.now(tz=UTC).date()
        end_date = start_date + timedelta(days=plan.period_days)

        membership = Membership(
            member_id=member_id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=end_date,
        )  # status defaults to PENDING — becomes ACTIVE once payment is recorded

        return self.membership_repository.create(membership)

    def get_my_membership(self, member_id: int) -> Membership:
        membership = self.membership_repository.get_active_by_member_id(member_id)
        if membership is None:
            raise MembershipNotFoundError
        return membership

    def freeze(self, membership_id: int, data: MembershipFreezeRequest) -> Membership:
        membership = self.membership_repository.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError

        membership.end_date = membership.end_date + timedelta(days=data.days)
        membership.status = MembershipStatus.FROZEN

        return self.membership_repository.update(membership)

    def unfreeze(self, membership_id: int) -> Membership:
        membership = self.membership_repository.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError

        membership.status = MembershipStatus.ACTIVE

        return self.membership_repository.update(membership)