# This gives us a contract without tying the service to one provider.

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass
class PaymentInitialization:
    provider: str
    checkout_url: str | None = None


class PaymentProvider(Protocol):
    @property
    def name(self) -> str: ...

    def initialize_payment(
        self,
        *,
        reference: str,
        amount: Decimal,
        email: str,
    ) -> PaymentInitialization: ...

# We didn’t make PaymentService depend directly on FakePaymentProvider because that would tightly couple the service to one implementation. We wanted the service to work with any provider that follows the same contract

#Protocol is basically saying: “Any object that has these required methods/properties can be treated as a payment provider.”