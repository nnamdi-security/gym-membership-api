from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.payment_repository import (
    PaymentRepository,
)


def create_membership_fixture(
    db_session,
) -> Membership:
    member = User(
        email="member@example.com",
        password_hash="hashed-password",
        role=UserRole.MEMBER,
    )

    plan = Plan(
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )

    db_session.add(member)
    db_session.add(plan)
    db_session.commit()

    db_session.refresh(member)
    db_session.refresh(plan)

    membership = Membership(
        member_id=member.id,
        plan_id=plan.id,
        status=MembershipStatus.PENDING_PAYMENT,
    )

    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)

    return membership


def test_create_payment(
    db_session,
):
    membership = create_membership_fixture(db_session)

    repository = PaymentRepository(db_session)

    payment = Payment(
        membership_id=membership.id,
        amount=Decimal("15000.00"),
        status=PaymentStatus.PENDING,
        method=PaymentMethod.ONLINE,
        reference="FITPRO-TEST-001",
        provider="test-provider",
    )

    created = repository.create(payment)

    assert created.id is not None
    assert created.membership_id == membership.id
    assert created.amount == Decimal("15000.00")
    assert created.status == PaymentStatus.PENDING
    assert created.reference == "FITPRO-TEST-001"


def test_get_payment_by_reference(
    db_session,
):
    membership = create_membership_fixture(db_session)

    repository = PaymentRepository(db_session)

    created = repository.create(
        Payment(
            membership_id=membership.id,
            amount=Decimal("15000.00"),
            status=PaymentStatus.PENDING,
            method=PaymentMethod.ONLINE,
            reference="FITPRO-TEST-002",
            provider="test-provider",
        )
    )

    found = repository.get_by_reference("FITPRO-TEST-002")

    assert found is not None
    assert found.id == created.id


def test_get_by_reference_returns_none_when_missing(
    db_session,
):
    repository = PaymentRepository(db_session)

    found = repository.get_by_reference("DOES-NOT-EXIST")

    assert found is None


def test_get_for_membership_returns_payment_history(
    db_session,
):
    membership = create_membership_fixture(db_session)

    repository = PaymentRepository(db_session)

    first = repository.create(
        Payment(
            membership_id=membership.id,
            amount=Decimal("15000.00"),
            status=PaymentStatus.FAILED,
            method=PaymentMethod.ONLINE,
            reference="FITPRO-TEST-003",
            provider="test-provider",
        )
    )

    second = repository.create(
        Payment(
            membership_id=membership.id,
            amount=Decimal("15000.00"),
            status=PaymentStatus.SUCCEEDED,
            method=PaymentMethod.CARD,
            reference="FITPRO-TEST-004",
            recorded_by=None,
        )
    )

    payments = repository.get_for_membership(membership.id)

    assert len(payments) == 2
    assert payments[0].id == second.id
    assert payments[1].id == first.id


def test_update_payment(
    db_session,
):
    membership = create_membership_fixture(db_session)

    repository = PaymentRepository(db_session)

    payment = repository.create(
        Payment(
            membership_id=membership.id,
            amount=Decimal("15000.00"),
            status=PaymentStatus.PENDING,
            method=PaymentMethod.ONLINE,
            reference="FITPRO-TEST-005",
            provider="test-provider",
        )
    )

    payment.status = PaymentStatus.SUCCEEDED

    updated = repository.update(payment)

    assert updated.status == PaymentStatus.SUCCEEDED


def test_duplicate_payment_reference_is_rejected(
    db_session,
):
    membership = create_membership_fixture(db_session)

    repository = PaymentRepository(db_session)

    repository.create(
        Payment(
            membership_id=membership.id,
            amount=Decimal("15000.00"),
            status=PaymentStatus.PENDING,
            method=PaymentMethod.ONLINE,
            reference="FITPRO-DUPLICATE",
            provider="test-provider",
        )
    )

    duplicate = Payment(
        membership_id=membership.id,
        amount=Decimal("15000.00"),
        status=PaymentStatus.PENDING,
        method=PaymentMethod.ONLINE,
        reference="FITPRO-DUPLICATE",
        provider="test-provider",
    )

    with pytest.raises(IntegrityError):
        repository.create(duplicate)

    db_session.rollback()
