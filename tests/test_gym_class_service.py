from datetime import UTC, datetime, timedelta
from app.services.noop_class_board_events import NoOpClassBoardEventPublisher

import pytest

from app.models.gym_class import GymClass
from app.schemas.gym_class import (
    GymClassCreateRequest,
    GymClassUpdateRequest,
)
from app.services.gym_class_service import (
    GymClassCapacityBelowAttendanceError,
    GymClassHasCheckinsError,
    GymClassNotFoundError,
    GymClassService,
    GymClassStartsInPastError,
)


class FakeGymClassRepository:
    def __init__(self):
        self.classes: dict[int, GymClass] = {}
        self.checkin_counts: dict[int, int] = {}
        self.next_id = 1

    def get_all(self) -> list[GymClass]:
        return list(self.classes.values())

    def get_by_id(
        self,
        class_id: int,
    ) -> GymClass | None:
        return self.classes.get(class_id)

    def count_checkins(
        self,
        class_id: int,
    ) -> int:
        return self.checkin_counts.get(
            class_id,
            0,
        )

    def create(
        self,
        gym_class: GymClass,
    ) -> GymClass:
        gym_class.id = self.next_id
        self.next_id += 1

        self.classes[gym_class.id] = gym_class

        return gym_class

    def update(
        self,
        gym_class: GymClass,
    ) -> GymClass:
        self.classes[gym_class.id] = gym_class
        return gym_class

    def delete(
        self,
        gym_class: GymClass,
    ) -> None:
        del self.classes[gym_class.id]


def test_create_future_class():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository, 
        class_board_event_publisher=NoOpClassBoardEventPublisher)

    starts_at = datetime.now(UTC) + timedelta(days=1)

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=starts_at,
        )
    )

    assert gym_class.id == 1
    assert gym_class.name == "Spin"
    assert gym_class.capacity == 12


def test_create_rejects_class_in_past():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    with pytest.raises(GymClassStartsInPastError):
        service.create_class(
            GymClassCreateRequest(
                name="Spin",
                capacity=12,
                starts_at=(datetime.now(UTC) - timedelta(hours=1)),
            )
        )


def test_get_class_raises_when_missing():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    with pytest.raises(GymClassNotFoundError):
        service.get_class(999)


def test_update_class_changes_only_supplied_fields():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    updated = service.update_class(
        gym_class.id,
        GymClassUpdateRequest(
            capacity=15,
        ),
    )

    assert updated.name == "Spin"
    assert updated.capacity == 15


def test_update_rejects_capacity_below_checkin_count():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    repository.checkin_counts[gym_class.id] = 10

    with pytest.raises(GymClassCapacityBelowAttendanceError):
        service.update_class(
            gym_class.id,
            GymClassUpdateRequest(
                capacity=9,
            ),
        )


def test_update_allows_capacity_equal_to_attendance():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    repository.checkin_counts[gym_class.id] = 10

    updated = service.update_class(
        gym_class.id,
        GymClassUpdateRequest(
            capacity=10,
        ),
    )

    assert updated.capacity == 10


def test_delete_unused_class():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Yoga",
            capacity=20,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    service.delete_class(gym_class.id)

    assert repository.get_by_id(gym_class.id) is None


def test_delete_rejects_class_with_checkins():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    repository.checkin_counts[gym_class.id] = 3

    with pytest.raises(GymClassHasCheckinsError):
        service.delete_class(gym_class.id)


def validate_future_datetime(
    self,
    starts_at: datetime,
) -> None:
    if starts_at.tzinfo is None:
        raise GymClassStartsInPastError

    if starts_at <= datetime.now(UTC):
        raise GymClassStartsInPastError


def test_get_class_board_returns_capacity_summary():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    repository.checkin_counts[gym_class.id] = 9

    board = service.get_class_board(gym_class.id)

    assert board.capacity == 12
    assert board.checked_in == 9
    assert board.remaining == 3
    assert board.full is False


def test_get_class_board_marks_full_class():
    repository = FakeGymClassRepository()
    service = GymClassService(
        repository,
        class_board_event_publisher=NoOpClassBoardEventPublisher
        )

    gym_class = service.create_class(
        GymClassCreateRequest(
            name="Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(days=1)),
        )
    )

    repository.checkin_counts[gym_class.id] = 12

    board = service.get_class_board(gym_class.id)

    assert board.remaining == 0
    assert board.full is True
