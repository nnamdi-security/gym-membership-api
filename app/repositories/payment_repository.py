# The repository's job is to persist and retrieve payment records. It should not decide whether a payment is valid, whether a membership may be activated, or whether an online callback is trustworthy. Those are service-layer concerns.

from sqlmodel import Session, select

from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        payment_id: int,
    ) -> Payment | None:
        return self.session.get(
            Payment,
            payment_id,
        )

    def get_by_reference(
        # The payment reference will become one of the most important lookup keys in the whole payment flow. It is how an external provider event gets tied back to our internal transaction.
        self,
        reference: str,
    ) -> Payment | None:
        statement = select(Payment).where(Payment.reference == reference)

        return self.session.exec(statement).first()

    def get_for_membership(
        self,
        membership_id: int,
    ) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.membership_id == membership_id)
            .order_by(Payment.id.desc())
        )

        return list(self.session.exec(statement).all())

    def create(
        self,
        payment: Payment,
    ) -> Payment:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)

        return payment

    def update(
        self,
        payment: Payment,
    ) -> Payment:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)

        return payment

    def get_succeeded_for_membership(
        self,
        membership_id: int,
    ) -> Payment | None:
        statement = (
            select(Payment)
            .where(
                Payment.membership_id == membership_id,
                Payment.status == PaymentStatus.SUCCEEDED,
            )
            .order_by(Payment.id.desc())
        )

        return self.session.exec(statement).first()

    # Non-committing repository methods which ensure that payment success and membership activation succeed or fail together.
    def add(
        self,
        payment: Payment,
    ) -> Payment:
        self.session.add(payment)

        return payment

    # Repository method for pending online payments
    def get_pending_online_for_membership(
        self,
        membership_id: int,
    ) -> Payment | None:
        statement = (
            select(Payment)
            .where(
                Payment.membership_id == membership_id,
                Payment.status == PaymentStatus.PENDING,
                Payment.method == PaymentMethod.ONLINE,
            )
            .order_by(Payment.id.desc())
        )

        return self.session.exec(statement).first()

    # Lock payment lookup
    def get_by_reference_for_update(
        self,
        reference: str,
    ) -> Payment | None:
        statement = (
            select(Payment).where(Payment.reference == reference).with_for_update()
        )

        return self.session.exec(statement).first()
