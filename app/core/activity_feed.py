from app.core.config import settings
from app.services.firestore_activity_feed import (
    FirestoreActivityFeedProjector,
)
from app.services.noop_activity_feed_projection import (
    NoOpActivityFeedProjector,
)


def get_activity_feed_projector():
    if settings.app_env == "test":
        return NoOpActivityFeedProjector()

    return FirestoreActivityFeedProjector()