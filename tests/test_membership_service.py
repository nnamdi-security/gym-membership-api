from datetime import date
from decimal import Decimal

import pytest

from app.models.membership import Membership, MembershipStatus
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.schemas.membership import (
    MembershipCreateForMemberRequest,
    MembershipCreateRequest,
)
from app.services.membership_service import (
    ActiveMembershipExistsError,
    InvalidMemberRoleError,
    MemberNotFoundError,
    MembershipCannotBeActivatedError,
    MembershipCannotBeFrozenError,
    MembershipCannotBeUnfrozenError,
    MembershipService,
    PendingMembershipExistsError,
    PlanNotFoundError,
)


class FakeMembershipRepository:
    def __init__(self):
        self.memberships: dict[int, Membership] = {}
        self.next_id = 1

    def get_by_id(
        self,
        membership_id: int,
    ) -> Membership | None:
        return self.memberships.get(membership_id)

    def get_for_member(
        self,
        member_id: int,
    ) -> list[Membership]:
        return [
            membership
            for membership in self.memberships.values()
            if membership.member_id == member_id
        ]

    def get_active_for_member(
        self,
        member_id: int,
    ) -> Membership | None:
        for membership in self.memberships.values():
            if (
                membership.member_id == member_id
                and membership.status == MembershipStatus.ACTIVE
            ):
                return membership

        return None

    def get_pending_for_member(
        self,
        member_id: int,
    ) -> Membership | None:
        for membership in self.memberships.values():
            if (
                membership.member_id == member_id
                and membership.status == MembershipStatus.PENDING_PAYMENT
            ):
                return membership

        return None

    def create(
        self,
        membership: Membership,
    ) -> Membership:
        membership.id = self.next_id
        self.next_id += 1

        self.memberships[membership.id] = membership

        return membership

    def update(
        self,
        membership: Membership,
    ) -> Membership:
        self.memberships[membership.id] = membership

        return membership


class FakePlanRepository:
    def __init__(self):
        self.plans: dict[int, Plan] = {}

    def get_by_id(
        self,
        plan_id: int,
    ) -> Plan | None:
        return self.plans.get(plan_id)


class FakeUserRepository:
    def __init__(self):
        self.users: dict[int, User] = {}

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        return self.users.get(user_id)


def build_service():
    membership_repository = FakeMembershipRepository()
    plan_repository = FakePlanRepository()
    user_repository = FakeUserRepository()

    user_repository.users[1] = User(
        id=1,
        email="member@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    plan_repository.plans[1] = Plan(
        id=1,
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )

    service = MembershipService(
        membership_repository,
        plan_repository,
        user_repository,
    )

    return (
        service,
        membership_repository,
        plan_repository,
        user_repository,
    )


def test_member_can_create_pending_membership():
    service, _, _, _ = build_service()

    membership = service.create_for_current_member(
        member_id=1,
        data=MembershipCreateRequest(
            plan_id=1,
        ),
    )

    assert membership.id == 1
    assert membership.member_id == 1
    assert membership.plan_id == 1
    assert membership.status == MembershipStatus.PENDING_PAYMENT
    assert membership.start_date is None
    assert membership.end_date is None


def test_create_rejects_missing_plan():
    service, _, _, _ = build_service()

    with pytest.raises(PlanNotFoundError):
        service.create_for_current_member(
            member_id=1,
            data=MembershipCreateRequest(
                plan_id=999,
            ),
        )


def test_create_rejects_missing_member():
    service, _, _, _ = build_service()

    with pytest.raises(MemberNotFoundError):
        service.create_for_current_member(
            member_id=999,
            data=MembershipCreateRequest(
                plan_id=1,
            ),
        )


def test_create_rejects_non_member_user():
    service, _, _, user_repository = build_service()

    user_repository.users[2] = User(
        id=2,
        email="admin@example.com",
        password_hash="hash",
        role=UserRole.ADMIN,
    )

    with pytest.raises(InvalidMemberRoleError):
        service.create_for_current_member(
            member_id=2,
            data=MembershipCreateRequest(
                plan_id=1,
            ),
        )


def test_create_rejects_member_with_active_membership():
    service, repository, _, _ = build_service()

    repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.ACTIVE,
        )
    )

    with pytest.raises(ActiveMembershipExistsError):
        service.create_for_current_member(
            member_id=1,
            data=MembershipCreateRequest(
                plan_id=1,
            ),
        )


def test_create_rejects_duplicate_pending_membership():
    service, _, _, _ = build_service()

    data = MembershipCreateRequest(
        plan_id=1,
    )

    service.create_for_current_member(
        member_id=1,
        data=data,
    )

    with pytest.raises(PendingMembershipExistsError):
        service.create_for_current_member(
            member_id=1,
            data=data,
        )


def test_staff_flow_can_create_pending_membership_for_member():
    service, _, _, _ = build_service()

    membership = service.create_for_member(
        MembershipCreateForMemberRequest(
            member_id=1,
            plan_id=1,
        )
    )

    assert membership.member_id == 1
    assert membership.status == MembershipStatus.PENDING_PAYMENT


def test_activate_membership_calculates_dates():
    service, _, _, _ = build_service()

    membership = service.create_for_current_member(
        member_id=1,
        data=MembershipCreateRequest(
            plan_id=1,
        ),
    )

    activated = service.activate_membership(
        membership.id,
        activation_date=date(2026, 9, 21),
    )

    assert activated.status == MembershipStatus.ACTIVE
    assert activated.start_date == date(2026, 9, 21)
    assert activated.end_date == date(2026, 10, 21)


def test_activate_rejects_non_pending_membership():
    service, repository, _, _ = build_service()

    membership = repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.ACTIVE,
        )
    )

    with pytest.raises(MembershipCannotBeActivatedError):
        service.activate_membership(
            membership.id,
            activation_date=date(2026, 9, 21),
        )


def test_freeze_active_membership():
    service, repository, _, _ = build_service()

    membership = repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.ACTIVE,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
        )
    )

    frozen = service.freeze_membership(
        membership.id,
        freeze_date=date(2026, 9, 10),
    )

    assert frozen.status == MembershipStatus.FROZEN


def test_freeze_rejects_pending_membership():
    service, repository, _, _ = build_service()

    membership = repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.PENDING_PAYMENT,
        )
    )

    with pytest.raises(MembershipCannotBeFrozenError):
        service.freeze_membership(
            membership.id,
            freeze_date=date(2026, 9, 10),
        )


def test_unfreeze_extends_end_date_by_frozen_days():
    service, repository, _, _ = build_service()

    membership = repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.FROZEN,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
            frozen_on=date(2026, 9, 10),
        )
    )

    unfrozen = service.unfreeze_membership(
        membership.id,
        unfreeze_date=date(2026, 9, 20),
    )

    assert unfrozen.status == MembershipStatus.ACTIVE
    assert unfrozen.frozen_on is None
    assert unfrozen.end_date == date(2026, 10, 11)


def test_unfreeze_rejects_non_frozen_membership():
    service, repository, _, _ = build_service()

    membership = repository.create(
        Membership(
            member_id=1,
            plan_id=1,
            status=MembershipStatus.ACTIVE,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
        )
    )

    with pytest.raises(MembershipCannotBeUnfrozenError):
        service.unfreeze_membership(
            membership.id,
            unfreeze_date=date(2026, 9, 20),
        )
