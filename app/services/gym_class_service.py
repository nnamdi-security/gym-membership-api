# This is where the repository’s database operations become real FitPro business rules.

# a new class session cannot normally be created in the past;
# a class must exist before it can be viewed/updated/deleted;
# capacity cannot be reduced below the number of existing check-ins;
# a class session with attendance history should not be deleted;
# updated_at should change when the class is modified.

import logging
from datetime import UTC, date, datetime

from app.models.gym_class import GymClass
from app.repositories.gym_class_repository import (
    GymClassRepository,
)
from app.schemas.class_board import ClassBoardResponse
from app.schemas.gym_class import (
    GymClassCreateRequest,
    GymClassUpdateRequest,
)
from app.services.class_board_event_publisher import (
    ClassBoardEventPublisher,
)

#from app.services.class_board_projection import ClassBoardProjector

logger = logging.getLogger(__name__)


class GymClassNotFoundError(Exception):
    pass


class GymClassStartsInPastError(Exception):
    pass


class GymClassCapacityBelowAttendanceError(Exception):
    pass


class GymClassHasCheckinsError(Exception):
    pass


class GymClassService:
    def __init__(
        self,
        repository: GymClassRepository,
        # class_board_projector: ClassBoardProjector,
        class_board_event_publisher: ClassBoardEventPublisher,
    ):
        self.repository = repository
        # self.class_board_projector = class_board_projector
        self.class_board_event_publisher = class_board_event_publisher

    def list_classes(
        self,
    ) -> list[GymClass]:
        return self.repository.get_all()

    def get_class(
        self,
        class_id: int,
    ) -> GymClass:
        gym_class = self.repository.get_by_id(class_id)

        if gym_class is None:
            raise GymClassNotFoundError

        return gym_class

    def create_class(
        self,
        data: GymClassCreateRequest,
    ) -> GymClass:
        now = datetime.now(UTC)

        if data.starts_at <= now:
            raise GymClassStartsInPastError

        gym_class = GymClass(
            name=data.name,
            capacity=data.capacity,
            starts_at=data.starts_at,
        )

        created = self.repository.create(gym_class)

        self._publish_board(created)

        return created

    def update_class(
        self,
        class_id: int,
        data: GymClassUpdateRequest,
    ) -> GymClass:
        gym_class = self.get_class(class_id)

        updates = data.model_dump(
            exclude_unset=True,
        )

        if "starts_at" in updates:
            starts_at = updates["starts_at"]

            if starts_at <= datetime.now(UTC):
                raise GymClassStartsInPastError

        if "capacity" in updates:
            current_count = self.repository.count_checkins(class_id)

            if updates["capacity"] < current_count:
                raise GymClassCapacityBelowAttendanceError

        for field, value in updates.items():
            setattr(
                gym_class,
                field,
                value,
            )

        gym_class.updated_at = datetime.now(UTC)

        updated = self.repository.update(gym_class)

        self._publish_board(updated)

        return updated

    def delete_class(
        self,
        class_id: int,
    ) -> None:
        gym_class = self.get_class(class_id)

        checkin_count = self.repository.count_checkins(class_id)

        if checkin_count > 0:
            raise GymClassHasCheckinsError

        class_id = gym_class.id

        self.repository.delete(gym_class)

    def get_class_board(
        self,
        class_id: int,
    ) -> ClassBoardResponse:
        gym_class = self.get_class(class_id)

        checked_in = self.repository.count_checkins(class_id)

        remaining = max(
            gym_class.capacity - checked_in,
            0,
        )

        return ClassBoardResponse(
            class_id=gym_class.id,
            name=gym_class.name,
            starts_at=gym_class.starts_at,
            capacity=gym_class.capacity,
            checked_in=checked_in,
            remaining=remaining,
            full=checked_in >= gym_class.capacity,
        )

    def get_class_board_for_date(
        self,
        target_date: date,
    ) -> list[ClassBoardResponse]:
        classes = self.repository.get_by_date(target_date)

        board: list[ClassBoardResponse] = []

        for gym_class in classes:
            checked_in = self.repository.count_checkins(gym_class.id)

            board.append(
                ClassBoardResponse(
                    class_id=gym_class.id,
                    name=gym_class.name,
                    starts_at=gym_class.starts_at,
                    capacity=gym_class.capacity,
                    checked_in=checked_in,
                    remaining=max(
                        gym_class.capacity - checked_in,
                        0,
                    ),
                    full=(checked_in >= gym_class.capacity),
                )
            )

        return board

    def _build_board_payload(
        self,
        gym_class: GymClass,
    ) -> dict:
        checked_in = self.repository.count_checkins(gym_class.id)

        remaining = max(
            gym_class.capacity - checked_in,
            0,
        )

        return {
            "event": "class.board.updated",
            "class_id": gym_class.id,
            "name": gym_class.name,
            "starts_at": gym_class.starts_at,
            "capacity": gym_class.capacity,
            "checked_in": checked_in,
            "remaining": remaining,
            "full": checked_in >= gym_class.capacity,
        }

    def _publish_board(
        self,
        gym_class: GymClass,
    ) -> None:
        payload = self._build_board_payload(gym_class)

        try:
            firestore_payload = {
                key: value for key, value in payload.items() if key != "event"
            }

            self.class_board_projector.publish(**firestore_payload)

        except Exception:
            logger.exception(
                "Failed to publish Firestore class board",
                extra={
                    "class_id": gym_class.id,
                },
            )

        try:
            self.class_board_event_publisher.publish(payload)

        except Exception:
            logger.exception(
                "Failed to publish Redis class-board event",
                extra={
                    "class_id": gym_class.id,
                },
            )

    def _delete_board_projection(
        self,
        class_id: int,
    ) -> None:
        try:
            self.class_board_projector.delete(class_id)

        except Exception:
            logger.exception(
                "Failed to delete Firestore class board",
                extra={
                    "class_id": class_id,
                },
            )

        try:
            self.class_board_event_publisher.delete(class_id)

        except Exception:
            logger.exception(
                "Failed to publish Redis class deletion event",
                extra={
                    "class_id": class_id,
                },
            )
