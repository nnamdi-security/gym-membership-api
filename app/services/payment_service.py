# This service should decide:

# whether the membership exists;
# whether it is still awaiting payment;
# whether the selected payment method is valid for staff use;
# how much should be charged;
# how to generate the payment reference;
# how to activate the membership after successful payment;
# how to avoid duplicate successful payments for the same pending membership.





from datetime import datetime, timezone, timedelta
from secrets import token_urlsafe

from app.models.membership import MembershipStatus
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)

from sqlmodel import Session

from app.repositories.membership_repository import (
    MembershipRepository,
)
from app.repositories.payment_repository import (
    PaymentRepository,
)
from app.repositories.plan_repository import PlanRepository
from app.schemas.payment import StaffPaymentRequest


class PaymentNotFoundError(Exception):
    pass


class MembershipNotFoundError(Exception):
    pass


class PlanNotFoundError(Exception):
    pass


class MembershipNotAwaitingPaymentError(Exception):
    pass


class InvalidStaffPaymentMethodError(Exception):
    pass


class MembershipAlreadyPaidError(Exception):
    pass


class PaymentService:
    def __init__(
        self,
        session: Session,
        payment_repository: PaymentRepository,
        membership_repository: MembershipRepository,
        plan_repository: PlanRepository,
    ):
        self.session = session
        self.payment_repository = payment_repository
        self.membership_repository = membership_repository
        self.plan_repository = plan_repository

    def get_payment(
        self,
        payment_id: int,
    ) -> Payment:
        payment = self.payment_repository.get_by_id(
            payment_id
        )

        if payment is None:
            raise PaymentNotFoundError

        return payment

    def get_membership_payments(
        self,
        membership_id: int,
    ) -> list[Payment]:
        membership = self.membership_repository.get_by_id(
            membership_id
        )

        if membership is None:
            raise MembershipNotFoundError

        return self.payment_repository.get_for_membership(
            membership_id
        )

    def record_staff_payment(
        self,
        data: StaffPaymentRequest,
        recorded_by: int,
    ) -> Payment:
        membership = self.membership_repository.get_by_id(
            data.membership_id
        )

        if membership is None:
            raise MembershipNotFoundError

        if (
            membership.status
            != MembershipStatus.PENDING_PAYMENT
        ):
            raise MembershipNotAwaitingPaymentError

        if data.method == PaymentMethod.ONLINE:
            raise InvalidStaffPaymentMethodError

        existing_payment = (
            self.payment_repository.get_succeeded_for_membership(
                membership.id
            )
        )

        if existing_payment is not None:
            raise MembershipAlreadyPaidError

        plan = self.plan_repository.get_by_id(
            membership.plan_id
        )

        if plan is None:
            raise PlanNotFoundError

        now = datetime.now(timezone.utc)

        payment = Payment(
            membership_id=membership.id,
            amount=plan.price,
            status=PaymentStatus.SUCCEEDED,
            method=data.method,
            reference=self._generate_reference(),
            provider=None,
            recorded_by=recorded_by,
            recorded_at=now,
            paid_at=now,
        )

        membership.start_date = now.date()
        membership.end_date = (
            now.date()
            + timedelta(
                days=plan.period_days
            )
        )
        membership.status = MembershipStatus.ACTIVE
        membership.updated_at = now

        try:
            self.payment_repository.add(payment)
            self.membership_repository.add(
                membership
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(payment)
        self.session.refresh(membership)

        return payment


    # The reference is: generated server-side; difficult to guess; highly unlikely to collide.

    # PostgreSQL still has: UNIQUE(reference) as the final guarantee.
    def _generate_reference(self) -> str:
        return f"FITPRO-{token_urlsafe(16)}"