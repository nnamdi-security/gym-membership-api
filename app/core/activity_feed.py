from app.core.config import settings
from app.services.activity_feed_projection import ActivityFeedProjector
from app.services.firestore_activity_feed import (
    FirestoreActivityFeedProjector,
)
from app.services.noop_activity_feed_projection import (
    NoOpActivityFeedProjector,
)


def get_activity_feed_projector() -> ActivityFeedProjector:
    if not settings.firestore_enabled:
        return NoOpActivityFeedProjector()

    if not settings.firestore_project_id:
        return NoOpActivityFeedProjector()

    return FirestoreActivityFeedProjector()
