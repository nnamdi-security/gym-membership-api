import pytest
from pydantic import ValidationError

from app.models.payment import PaymentMethod
from app.schemas.payment import StaffPaymentRequest


def test_staff_payment_accepts_valid_request():
    data = StaffPaymentRequest(
        membership_id=1,
        method=PaymentMethod.CASH,
    )

    assert data.membership_id == 1
    assert data.method == PaymentMethod.CASH


def test_staff_payment_rejects_invalid_membership_id():
    with pytest.raises(ValidationError):
        StaffPaymentRequest(
            membership_id=0,
            method=PaymentMethod.CASH,
        )


def test_staff_payment_rejects_extra_amount():
    with pytest.raises(ValidationError):
        StaffPaymentRequest(
            membership_id=1,
            method=PaymentMethod.CASH,
            amount="1.00",
        )













# create PENDING payment
# ↓
# provider
# ↓
# webhook
# ↓
# verify signature
# ↓
# find reference
# ↓
# if already processed → 200, do nothing
# ↓
# mark payment SUCCEEDED
# ↓
# activate membership
# ↓
# record processed_event
# ↓
# commit transaction