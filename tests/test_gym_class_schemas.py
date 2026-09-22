from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.gym_class import (
    GymClassCreateRequest,
    GymClassUpdateRequest,
)


def test_class_create_accepts_valid_data():
    starts_at = datetime(
        2026,
        9,
        22,
        18,
        0,
        tzinfo=timezone.utc,
    )

    data = GymClassCreateRequest(
        name="Spin",
        capacity=12,
        starts_at=starts_at,
    )

    assert data.name == "Spin"
    assert data.capacity == 12
    assert data.starts_at == starts_at


def test_class_create_rejects_zero_capacity():
    with pytest.raises(ValidationError):
        GymClassCreateRequest(
            name="Spin",
            capacity=0,
            starts_at=datetime.now(timezone.utc),
        )


def test_class_create_rejects_negative_capacity():
    with pytest.raises(ValidationError):
        GymClassCreateRequest(
            name="Spin",
            capacity=-1,
            starts_at=datetime.now(timezone.utc),
        )


def test_class_update_allows_partial_changes():
    data = GymClassUpdateRequest(
        capacity=15,
    )

    assert data.name is None
    assert data.capacity == 15
    assert data.starts_at is None


