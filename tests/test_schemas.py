from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.plan import (
    PlanCreateRequest,
    PlanUpdateRequest,
)


def test_plan_create_accepts_valid_data():
    plan = PlanCreateRequest(
        name="Monthly",
        price=Decimal("15000.00"),
        period_days=30,
    )

    assert plan.name == "Monthly"
    assert plan.price == Decimal("15000.00")
    assert plan.period_days == 30


def test_plan_create_rejects_zero_price():
    with pytest.raises(ValidationError):
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("0.00"),
            period_days=30,
        )


def test_plan_create_rejects_negative_price():
    with pytest.raises(ValidationError):
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("-100.00"),
            period_days=30,
        )


def test_plan_create_rejects_zero_period():
    with pytest.raises(ValidationError):
        PlanCreateRequest(
            name="Monthly",
            price=Decimal("15000.00"),
            period_days=0,
        )


def test_plan_update_allows_partial_data():
    plan = PlanUpdateRequest(
        price=Decimal("17000.00"),
    )

    assert plan.name is None
    assert plan.price == Decimal("17000.00")
    assert plan.period_days is None
