import pytest
from sqlalchemy.exc import IntegrityError

from app.models.processed_event import ProcessedEvent
from app.repositories.processed_event_repository import (
    ProcessedEventRepository,
)


def test_create_processed_event(
    db_session,
):
    repository = ProcessedEventRepository(db_session)

    event = ProcessedEvent(
        event_id="evt_test_001",
        reference="FITPRO-TEST-001",
    )

    created = repository.create(event)

    assert created.id is not None
    assert created.event_id == "evt_test_001"
    assert created.reference == "FITPRO-TEST-001"


def test_get_processed_event_by_event_id(
    db_session,
):
    repository = ProcessedEventRepository(db_session)

    created = repository.create(
        ProcessedEvent(
            event_id="evt_test_002",
            reference="FITPRO-TEST-002",
        )
    )

    found = repository.get_by_event_id("evt_test_002")

    assert found is not None
    assert found.id == created.id


def test_get_processed_event_returns_none_when_missing(
    db_session,
):
    repository = ProcessedEventRepository(db_session)

    found = repository.get_by_event_id("evt_missing")

    assert found is None


def test_duplicate_event_id_is_rejected(
    db_session,
):
    repository = ProcessedEventRepository(db_session)

    repository.create(
        ProcessedEvent(
            event_id="evt_duplicate",
            reference="FITPRO-001",
        )
    )

    duplicate = ProcessedEvent(
        event_id="evt_duplicate",
        reference="FITPRO-001",
    )

    with pytest.raises(IntegrityError):
        repository.create(duplicate)

    db_session.rollback()
