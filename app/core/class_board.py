from app.core.config import settings
from app.services.class_board_projection import ClassBoardProjector
from app.services.firestore_class_board import (
    FirestoreClassBoardProjector,
)
from app.services.noop_class_board_projection import (
    NoOpClassBoardProjector,
)


def get_class_board_projector() -> ClassBoardProjector:
    if not settings.firestore_enabled:
        return NoOpClassBoardProjector()

    if not settings.firestore_project_id:
        return NoOpClassBoardProjector()

    return FirestoreClassBoardProjector()