from decimal import Decimal

import pytest
from sqlmodel import Session

from app.db.session import engine
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
from app.schemas.payment import StaffPaymentRequest
from app.services.payment_service import (
    InvalidStaffPaymentMethodError,
    MembershipNotAwaitingPaymentError,
    PaymentService,
)



def create_pending_membership(
    session: Session,
) -> tuple[User, Plan, Membership]:
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

    return staff, plan, membership




def test_staff_payment_activates_membership_atomically(
    db_session,
):
    staff, plan, membership = (
        create_pending_membership(
            db_session
        )
    )

    service = PaymentService(
        session=db_session,
        payment_repository=PaymentRepository(
            db_session
        ),
        membership_repository=MembershipRepository(
            db_session
        ),
        plan_repository=PlanRepository(
            db_session
        ),
    )

    payment = service.record_staff_payment(
        StaffPaymentRequest(
            membership_id=membership.id,
            method=PaymentMethod.CASH,
        ),
        recorded_by=staff.id,
    )

    assert payment.id is not None
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.amount == plan.price
    assert payment.recorded_by == staff.id
    assert payment.paid_at is not None

    db_session.refresh(membership)

    assert (
        membership.status
        == MembershipStatus.ACTIVE
    )
    assert membership.start_date is not None
    assert membership.end_date is not None




def test_staff_payment_uses_plan_price(
    db_session,
):
    staff, plan, membership = (
        create_pending_membership(
            db_session
        )
    )

    service = PaymentService(
        session=db_session,
        payment_repository=PaymentRepository(
            db_session
        ),
        membership_repository=MembershipRepository(
            db_session
        ),
        plan_repository=PlanRepository(
            db_session
        ),
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
    staff, _, membership = (
        create_pending_membership(
            db_session
        )
    )

    service = PaymentService(
        session=db_session,
        payment_repository=PaymentRepository(
            db_session
        ),
        membership_repository=MembershipRepository(
            db_session
        ),
        plan_repository=PlanRepository(
            db_session
        ),
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
    staff, _, membership = (
        create_pending_membership(
            db_session
        )
    )

    membership.status = MembershipStatus.ACTIVE
    db_session.add(membership)
    db_session.commit()

    service = PaymentService(
        session=db_session,
        payment_repository=PaymentRepository(
            db_session
        ),
        membership_repository=MembershipRepository(
            db_session
        ),
        plan_repository=PlanRepository(
            db_session
        ),
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



def build_payment_service(
    session: Session,
) -> PaymentService:
    return PaymentService(
        session=session,
        payment_repository=PaymentRepository(session),
        membership_repository=MembershipRepository(session),
        plan_repository=PlanRepository(session),
    )