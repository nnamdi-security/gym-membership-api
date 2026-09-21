from datetime import UTC, date, datetime, timedelta, timezone

from app.models.membership import Membership, MembershipStatus
from app.models.user import UserRole
from app.repositories.membership_repository import MembershipRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.user import UserRepository
from app.schemas.membership import (
    MembershipCreateForMemberRequest,
    MembershipCreateRequest,
)


class MembershipNotFoundError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


class InvalidMemberRoleError(Exception):
    pass


class PlanNotFoundError(Exception):
    pass


class CurrentMembershipExistsError(Exception):
    pass


class PendingMembershipExistsError(Exception):
    pass


class MembershipCannotBeActivatedError(Exception):
    pass


class MembershipCannotBeFrozenError(Exception):
    pass


class MembershipCannotBeUnfrozenError(Exception):
    pass


class MembershipService:
    def __init__(
        self,
        membership_repository: MembershipRepository,
        plan_repository: PlanRepository,
        user_repository: UserRepository,
    ):
        self.membership_repository = membership_repository
        self.plan_repository = plan_repository
        self.user_repository = user_repository

    def create_for_current_member(
        self,
        member_id: int,
        data: MembershipCreateRequest,
    ) -> Membership:
        return self._create_pending_membership(
            member_id=member_id,
            plan_id=data.plan_id,
        )

    def create_for_member(
        self,
        data: MembershipCreateForMemberRequest,
    ) -> Membership:
        return self._create_pending_membership(
            member_id=data.member_id,
            plan_id=data.plan_id,
        )

    def get_membership(
        self,
        membership_id: int,
    ) -> Membership:
        membership = self.membership_repository.get_by_id(membership_id)

        if membership is None:
            raise MembershipNotFoundError

        return membership

    def get_member_history(
        self,
        member_id: int,
    ) -> list[Membership]:
        self._validate_member(member_id)

        return self.membership_repository.get_for_member(member_id)

    def activate_membership(
        self,
        membership_id: int,
        activation_date: date | None = None,
    ) -> Membership:
        membership = self.get_membership(membership_id)

        if membership.status != MembershipStatus.PENDING_PAYMENT:
            raise MembershipCannotBeActivatedError

        plan = self.plan_repository.get_by_id(membership.plan_id)

        if plan is None:
            raise PlanNotFoundError

        start_date = activation_date or datetime.now(timezone.UTC).date()

        membership.start_date = start_date
        membership.end_date = start_date + timedelta(days=plan.period_days)
        membership.status = MembershipStatus.ACTIVE
        membership.updated_at = datetime.now(timezone.UTC)

        return self.membership_repository.update(membership)

    def _create_pending_membership(
        self,
        member_id: int,
        plan_id: int,
    ) -> Membership:
        self._validate_member(member_id)

        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None:
            raise PlanNotFoundError

        current_membership = self.membership_repository.get_current_for_member(
            member_id
        )

        if current_membership is not None:
            raise CurrentMembershipExistsError

        pending_membership = self.membership_repository.get_pending_for_member(
            member_id
        )

        if pending_membership is not None:
            raise PendingMembershipExistsError

        membership = Membership(
            member_id=member_id,
            plan_id=plan_id,
            status=MembershipStatus.PENDING_PAYMENT,
        )

        return self.membership_repository.create(membership)

    def _validate_member(
        self,
        member_id: int,
    ) -> None:
        user = self.user_repository.get_by_id(member_id)

        if user is None:
            raise MemberNotFoundError

        if user.role != UserRole.MEMBER:
            raise InvalidMemberRoleError

    def freeze_membership(
        self,
        membership_id: int,
        freeze_date: date | None = None,
    ) -> Membership:
        membership = self.get_membership(membership_id)

        if membership.status != MembershipStatus.ACTIVE:
            raise MembershipCannotBeFrozenError

        if membership.start_date is None or membership.end_date is None:
            raise MembershipCannotBeFrozenError

        effective_date = freeze_date or date.today()

        if effective_date < membership.start_date:
            raise MembershipCannotBeFrozenError

        if effective_date >= membership.end_date:
            raise MembershipCannotBeFrozenError

        membership.status = MembershipStatus.FROZEN
        membership.frozen_on = effective_date
        membership.updated_at = datetime.now(UTC)

        return self.membership_repository.update(membership)

    def unfreeze_membership(
        self,
        membership_id: int,
        unfreeze_date: date | None = None,
    ) -> Membership:
        membership = self.get_membership(membership_id)

        if membership.status != MembershipStatus.FROZEN:
            raise MembershipCannotBeUnfrozenError

        if membership.frozen_on is None:
            raise MembershipCannotBeUnfrozenError

        if membership.end_date is None:
            raise MembershipCannotBeUnfrozenError

        effective_date = unfreeze_date or date.today()

        if effective_date < membership.frozen_on:
            raise MembershipCannotBeUnfrozenError

        frozen_days = (effective_date - membership.frozen_on).days

        membership.end_date = membership.end_date + timedelta(days=frozen_days)

        membership.status = MembershipStatus.ACTIVE
        membership.frozen_on = None
        membership.updated_at = datetime.now(UTC)

        return self.membership_repository.update(membership)
