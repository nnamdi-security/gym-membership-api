from decimal import Decimal

import pytest
from sqlmodel import Session

from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.payment import (
    PaymentMethod,
    PaymentStatus,
)
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.membership_repository import (
    MembershipRepository,
)
from app.repositories.payment_repository import (
    PaymentRepository,
)
from app.repositories.plan_repository import PlanRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payment import StaffPaymentRequest
from app.services.noop_activity_feed_projection import (
    NoOpActivityFeedProjector,
)
from app.services.payment_provider import (
    PaymentInitialization,
)
from app.services.payment_service import (
    InvalidStaffPaymentMethodError,
    MembershipNotAwaitingPaymentError,
    MembershipNotFoundError,
    PaymentService,
    PendingOnlinePaymentExistsError,
)


class FakeProvider:
    @property
    def name(self) -> str:
        return "test-provider"

    def initialize_payment(
        self,
        *,
        reference,
        amount,
        email,
    ):
        return PaymentInitialization(
            provider=self.name,
            checkout_url=(
                f"https://provider.test/{reference}"
            ),
        )


def create_pending_membership(
    session: Session,
) -> tuple[User, User, Plan, Membership]:
    member = User(
        email="member@example.com",
        password_hash="hashed",
        role=UserRole.MEMBER,
    )

    staff = User(
        email="staff@example.com",
        password_hash="hashed",
        role=UserRole.FRONT_DESK,
    )

    plan = Plan(
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )

    session.add(member)
    session.add(staff)
    session.add(plan)
    session.commit()

    session.refresh(member)
    session.refresh(staff)
    session.refresh(plan)

    membership = Membership(
        member_id=member.id,
        plan_id=plan.id,
        status=MembershipStatus.PENDING_PAYMENT,
    )

    session.add(membership)
    session.commit()
    session.refresh(membership)

    return (
        staff,
        member,
        plan,
        membership,
    )


def build_payment_service(
    session: Session,
) -> PaymentService:
    return PaymentService(
        session=session,
        payment_repository=PaymentRepository(session),
        membership_repository=MembershipRepository(session),
        plan_repository=PlanRepository(session),
        user_repository=UserRepository(session),
        payment_provider=FakeProvider(),
        activity_feed_projector=(
            NoOpActivityFeedProjector()
        ),
    )


def test_staff_payment_activates_membership_atomically(
    db_session,
):
    (
        staff,
        _,
        plan,
        membership,
    ) = create_pending_membership(
        db_session
    )

    service = build_payment_service(
        db_session
    )

    payment = service.record_staff_payment(
        StaffPaymentRequest(
            membership_id=membership.id,
            method=PaymentMethod.CASH,
        ),
        recorded_by=staff.id,
    )

    assert payment.id is not None
    assert (
        payment.status
        == PaymentStatus.SUCCEEDED
    )
    assert payment.amount == plan.price
    assert payment.recorded_by == staff.id
    assert payment.paid_at is not None

    db_session.refresh(
        membership
    )

    assert (
        membership.status
        == MembershipStatus.ACTIVE
    )
    assert membership.start_date is not None
    assert membership.end_date is not None


def test_staff_payment_uses_plan_price(
    db_session,
):
    (
        staff,
        _,
        plan,
        membership,
    ) = create_pending_membership(
        db_session
    )

    service = build_payment_service(
        db_session
    )

    payment = service.record_staff_payment(
        StaffPaymentRequest(
            membership_id=membership.id,
            method=PaymentMethod.TRANSFER,
        ),
        recorded_by=staff.id,
    )

    assert payment.amount == plan.price


def test_staff_payment_rejects_online_method(
    db_session,
):
    (
        staff,
        _,
        _,
        membership,
    ) = create_pending_membership(
        db_session
    )

    service = build_payment_service(
        db_session
    )

    with pytest.raises(
        InvalidStaffPaymentMethodError
    ):
        service.record_staff_payment(
            StaffPaymentRequest(
                membership_id=membership.id,
                method=PaymentMethod.ONLINE,
            ),
            recorded_by=staff.id,
        )


def test_payment_rejects_membership_not_awaiting_payment(
    db_session,
):
    (
        staff,
        _,
        _,
        membership,
    ) = create_pending_membership(
        db_session
    )

    membership.status = (
        MembershipStatus.ACTIVE
    )

    db_session.add(
        membership
    )
    db_session.commit()

    service = build_payment_service(
        db_session
    )

    with pytest.raises(
        MembershipNotAwaitingPaymentError
    ):
        service.record_staff_payment(
            StaffPaymentRequest(
                membership_id=membership.id,
                method=PaymentMethod.CASH,
            ),
            recorded_by=staff.id,
        )


def test_online_initialization_creates_pending_payment(
    db_session,
):
    (
        _,
        member,
        plan,
        membership,
    ) = create_pending_membership(
        db_session
    )

    service = build_payment_service(
        db_session
    )

    result = service.initialize_online_payment(
        membership_id=membership.id,
        member_id=member.id,
    )

    assert (
        result.payment.status
        == PaymentStatus.PENDING
    )
    assert (
        result.payment.method
        == PaymentMethod.ONLINE
    )
    assert (
        result.payment.amount
        == plan.price
    )
    assert (
        result.payment.recorded_by
        is None
    )
    assert (
        result.payment.paid_at
        is None
    )
    assert result.checkout_url is not None

    db_session.refresh(
        membership
    )

    assert (
        membership.status
        == MembershipStatus.PENDING_PAYMENT
    )


def test_online_initialization_rejects_duplicate_pending_attempt(
    db_session,
):
    (
        _,
        member,
        _,
        membership,
    ) = create_pending_membership(
        db_session
    )

    service = build_payment_service(
        db_session
    )

    service.initialize_online_payment(
        membership_id=membership.id,
        member_id=member.id,
    )

    with pytest.raises(
        PendingOnlinePaymentExistsError
    ):
        service.initialize_online_payment(
            membership_id=membership.id,
            member_id=member.id,
        )


def test_online_initialization_rejects_another_members_membership(
    db_session,
):
    (
        _,
        _,
        _,
        membership,
    ) = create_pending_membership(
        db_session
    )

    other = User(
        email="other@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    db_session.add(
        other
    )
    db_session.commit()
    db_session.refresh(
        other
    )

    service = build_payment_service(
        db_session
    )

    with pytest.raises(
        MembershipNotFoundError
    ):
        service.initialize_online_payment(
            membership_id=membership.id,
            member_id=other.id,
        )