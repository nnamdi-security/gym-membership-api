import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from app.models.membership import MembershipStatus
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.processed_event import ProcessedEvent
from app.repositories.membership_repository import MembershipRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.processed_event_repository import (
    ProcessedEventRepository,
)
from app.schemas.webhook import PaymentWebhookEvent


logger = logging.getLogger(__name__)


class WebhookPaymentMismatchError(Exception):
    pass


@dataclass
class WebhookProcessResult:
    status: str


class WebhookService:
    def __init__(
        self,
        session: Session,
        payment_repository: PaymentRepository,
        membership_repository: MembershipRepository,
        plan_repository: PlanRepository,
        processed_event_repository: ProcessedEventRepository,
    ):
        self.session = session
        self.payment_repository = payment_repository
        self.membership_repository = membership_repository
        self.plan_repository = plan_repository
        self.processed_event_repository = (
            processed_event_repository
        )

    def process_payment_event(
        self,
        event: PaymentWebhookEvent,
    ) -> WebhookProcessResult:
        existing_event = (
            self.processed_event_repository.get_by_event_id(
                event.event_id
            )
        )

        if existing_event is not None:
            return WebhookProcessResult(
                status="duplicate"
            )

        if event.event_type != "payment.succeeded":
            return self._record_ignored_event(event)

        payment = (
            self.payment_repository.get_by_reference_for_update(
                event.reference
            )
        )

        if payment is None:
            return self._record_orphan_event(event)

        self._validate_payment_event(
            event=event,
            payment=payment,
        )

        if payment.status == PaymentStatus.SUCCEEDED:
            return self._record_already_confirmed_event(
                event
            )

        membership = self.membership_repository.get_by_id(
            payment.membership_id
        )

        if membership is None:
            raise WebhookPaymentMismatchError

        if (
            membership.status
            != MembershipStatus.PENDING_PAYMENT
        ):
            raise WebhookPaymentMismatchError

        plan = self.plan_repository.get_by_id(
            membership.plan_id
        )

        if plan is None:
            raise WebhookPaymentMismatchError

        paid_at = event.paid_at

        if paid_at.tzinfo is None:
            paid_at = paid_at.replace(
                tzinfo=timezone.utc
            )

        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = paid_at

        activation_date = paid_at.date()

        membership.start_date = activation_date
        membership.end_date = (
            activation_date
            + timedelta(
                days=plan.period_days
            )
        )
        membership.status = MembershipStatus.ACTIVE
        membership.updated_at = datetime.now(
            timezone.utc
        )

        processed_event = ProcessedEvent(
            event_id=event.event_id,
            reference=event.reference,
        )

        try:
            self.payment_repository.add(payment)
            self.membership_repository.add(
                membership
            )
            self.processed_event_repository.add(
                processed_event
            )

            self.session.commit()

        except IntegrityError:
            self.session.rollback()

            duplicate = (
                self.processed_event_repository.get_by_event_id(
                    event.event_id
                )
            )

            if duplicate is not None:
                return WebhookProcessResult(
                    status="duplicate"
                )

            raise

        except SQLAlchemyError:
            self.session.rollback()
            raise

        return WebhookProcessResult(
            status="processed"
        )

    def _validate_payment_event(
        self,
        *,
        event: PaymentWebhookEvent,
        payment,
    ) -> None:
        if payment.method != PaymentMethod.ONLINE:
            raise WebhookPaymentMismatchError

        expected_amount = int(
            payment.amount * Decimal("100")
        )

        if event.amount != expected_amount:
            raise WebhookPaymentMismatchError

        if event.currency.upper() != "NGN":
            raise WebhookPaymentMismatchError

    def _record_orphan_event(
        self,
        event: PaymentWebhookEvent,
    ) -> WebhookProcessResult:
        logger.warning(
            "Received payment webhook for unknown reference %s",
            event.reference,
        )

        self._record_processed_event(event)

        return WebhookProcessResult(
            status="orphan"
        )

    def _record_ignored_event(
        self,
        event: PaymentWebhookEvent,
    ) -> WebhookProcessResult:
        self._record_processed_event(event)

        return WebhookProcessResult(
            status="ignored"
        )

    def _record_already_confirmed_event(
        self,
        event: PaymentWebhookEvent,
    ) -> WebhookProcessResult:
        self._record_processed_event(event)

        return WebhookProcessResult(
            status="already_confirmed"
        )

    def _record_processed_event(
        self,
        event: PaymentWebhookEvent,
    ) -> None:
        processed_event = ProcessedEvent(
            event_id=event.event_id,
            reference=event.reference,
        )

        try:
            self.processed_event_repository.add(
                processed_event
            )
            self.session.commit()

        except IntegrityError:
            self.session.rollback()

        except SQLAlchemyError:
            self.session.rollback()
            raise