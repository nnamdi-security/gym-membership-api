from dataclasses import dataclass
from datetime import UTC, datetime, timedelta,timezone
from secrets import token_urlsafe
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.models.membership import MembershipStatus, Membership
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.repositories.membership_repository import MembershipRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payment import StaffPaymentRequest
from app.services.payment_provider import PaymentProvider


logger = logging.getLogger(__name__)

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


class PendingOnlinePaymentExistsError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


@dataclass
class OnlinePaymentResult:
    payment: Payment
    checkout_url: str | None


class PaymentService:
    def __init__(
        self,
        session: Session,
        payment_repository: PaymentRepository,
        membership_repository: MembershipRepository,
        plan_repository: PlanRepository,
        user_repository: UserRepository,
        payment_provider: PaymentProvider,
        activity_feed_projector,
    ):
        self.session = session
        self.payment_repository = payment_repository
        self.membership_repository = membership_repository
        self.plan_repository = plan_repository
        self.user_repository = user_repository
        self.payment_provider = payment_provider
        self.activity_feed_projector = activity_feed_projector

    def get_payment(
        self,
        payment_id: int,
    ) -> Payment:
        payment = self.payment_repository.get_by_id(payment_id)

        if payment is None:
            raise PaymentNotFoundError

        return payment

    def get_membership_payments(
        self,
        membership_id: int,
    ) -> list[Payment]:
        membership = self.membership_repository.get_by_id(membership_id)

        if membership is None:
            raise MembershipNotFoundError

        return self.payment_repository.get_for_membership(membership_id)

    def record_staff_payment(
        self,
        data: StaffPaymentRequest,
        recorded_by: int,
    ) -> Payment:
        membership = self.membership_repository.get_by_id(data.membership_id)

        if membership is None:
            raise MembershipNotFoundError

        if membership.status != MembershipStatus.PENDING_PAYMENT:
            raise MembershipNotAwaitingPaymentError

        if data.method == PaymentMethod.ONLINE:
            raise InvalidStaffPaymentMethodError

        existing_payment = self.payment_repository.get_succeeded_for_membership(
            membership.id
        )

        if existing_payment is not None:
            raise MembershipAlreadyPaidError

        plan = self.plan_repository.get_by_id(membership.plan_id)

        if plan is None:
            raise PlanNotFoundError

        now = datetime.now(UTC)

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
        membership.end_date = now.date() + timedelta(days=plan.period_days)
        membership.status = MembershipStatus.ACTIVE
        membership.updated_at = now

        try:
            self.payment_repository.add(payment)
            self.membership_repository.add(membership)

            self.session.commit()

        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(payment)
        self.session.refresh(membership)
        self._publish_membership_activation(
            payment=payment,
            membership=membership,
        )

        return payment

    def initialize_online_payment(
        self,
        membership_id: int,
        member_id: int,
    ) -> OnlinePaymentResult:
        membership = self.membership_repository.get_by_id(membership_id)

        if membership is None:
            raise MembershipNotFoundError

        if membership.member_id != member_id:
            raise MembershipNotFoundError

        if membership.status != MembershipStatus.PENDING_PAYMENT:
            raise MembershipNotAwaitingPaymentError

        existing_pending = self.payment_repository.get_pending_online_for_membership(
            membership.id
        )

        if existing_pending is not None:
            raise PendingOnlinePaymentExistsError

        plan = self.plan_repository.get_by_id(membership.plan_id)

        if plan is None:
            raise PlanNotFoundError

        member = self.user_repository.get_by_id(member_id)

        if member is None:
            raise MemberNotFoundError

        reference = self._generate_reference()

        initialization = self.payment_provider.initialize_payment(
            reference=reference,
            amount=plan.price,
            email=member.email,
        )

        payment = Payment(
            membership_id=membership.id,
            amount=plan.price,
            status=PaymentStatus.PENDING,
            method=PaymentMethod.ONLINE,
            reference=reference,
            provider=initialization.provider,
            recorded_by=None,
            paid_at=None,
        )

        created_payment = self.payment_repository.create(payment)

        return OnlinePaymentResult(
            payment=created_payment,
            checkout_url=initialization.checkout_url,
        )

    def _generate_reference(self) -> str:
        return f"FITPRO-{token_urlsafe(16)}"

    def _publish_membership_activation(
        self,
        *,
        payment: Payment,
        membership,
    ) -> None:
        try:
            self.activity_feed_projector.publish(
                event_type="membership.activated",
                occurred_at=payment.paid_at,
                message=(f"Membership {membership.id} was activated"),
                data={
                    "membership_id": membership.id,
                    "payment_id": payment.id,
                    "member_id": membership.member_id,
                },
            )

        except Exception:
            logger.exception(
                "Failed to publish membership activation event",
                extra={
                    "membership_id": membership.id,
                    "payment_id": payment.id,
                },
            )
