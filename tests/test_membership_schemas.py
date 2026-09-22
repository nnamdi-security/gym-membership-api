from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.membership import MembershipStatus
from app.schemas.membership import (
    MembershipCreateForMemberRequest,
    MembershipCreateRequest,
    MembershipResponse,
)


def test_membership_create_accepts_plan():
    data = MembershipCreateRequest(
        plan_id=2,
    )

    assert data.plan_id == 2


def test_membership_create_rejects_invalid_plan_id():
    with pytest.raises(ValidationError):
        MembershipCreateRequest(
            plan_id=0,
        )


def test_member_cannot_supply_member_id():
    with pytest.raises(ValidationError):
        MembershipCreateRequest(
            plan_id=2,
            member_id=999,
        )


def test_member_cannot_supply_start_date():
    with pytest.raises(ValidationError):
        MembershipCreateRequest(
            plan_id=2,
            start_date="2026-09-21",
        )


def test_member_cannot_supply_end_date():
    with pytest.raises(ValidationError):
        MembershipCreateRequest(
            plan_id=2,
            end_date="2099-01-01",
        )


def test_staff_create_accepts_member_and_plan():
    data = MembershipCreateForMemberRequest(
        member_id=10,
        plan_id=2,
    )

    assert data.member_id == 10
    assert data.plan_id == 2


def test_pending_membership_response_allows_empty_dates():
    now = datetime.now(UTC)

    response = MembershipResponse(
        id=1,
        member_id=10,
        plan_id=2,
        start_date=None,
        end_date=None,
        frozen_on=None,
        status=MembershipStatus.PENDING_PAYMENT,
        created_at=now,
        updated_at=now,
    )

    assert response.status == MembershipStatus.PENDING_PAYMENT
    assert response.start_date is None
    assert response.end_date is None
