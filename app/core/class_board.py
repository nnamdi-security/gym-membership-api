from app.core.config import settings
from app.services.firestore_class_board import (
    FirestoreClassBoardProjector,
)
from app.services.noop_class_board_projection import (
    NoOpClassBoardProjector,
)


def get_class_board_projector():
    if settings.app_env == "test":
        return NoOpClassBoardProjector()

    return FirestoreClassBoardProjector()