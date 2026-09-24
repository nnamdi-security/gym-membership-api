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
