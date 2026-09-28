from decimal import Decimal

from app.services.payment_provider import (
    PaymentInitialization,
)

# This is a fake implementation of a payment provider used for development and testing. It lets the rest of FitPro behave as if it is talking to a real provider such as Paystack or Flutterwave, without making any real external API call.
class FakePaymentProvider:
    @property               #It lets a method be accessed like an attribute. It is useful when the value conceptually behaves like data rather than an action.
    def name(self) -> str:
        return "fake-provider"

    def initialize_payment(
        self,
        *,         #It means everything after it must be passed as a keyword argument.
        reference: str,
        amount: Decimal,
        email: str,
    ) -> PaymentInitialization:
        return PaymentInitialization(
            provider=self.name,
            checkout_url=(f"https://example.test/pay/{reference}"),
        )
