from decimal import Decimal

from app.services.payment_provider import (
    PaymentInitialization,
)


class FakePaymentProvider:
    @property
    def name(self) -> str:
        return "fake-provider"

    def initialize_payment(
        self,
        *,
        reference: str,
        amount: Decimal,
        email: str,
    ) -> PaymentInitialization:
        return PaymentInitialization(
            provider=self.name,
            checkout_url=(f"https://example.test/pay/{reference}"),
        )
