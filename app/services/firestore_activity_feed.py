from uuid import uuid4

from google.cloud import firestore

from app.core.config import settings


class FirestoreActivityFeedProjector:
    COLLECTION_NAME = "activity_feed"

    def __init__(self):
        self.client = firestore.Client(
            project=settings.firestore_project_id,
        )

    def publish(
        self,
        *,
        event_type: str,
        occurred_at,
        message: str,
        data: dict,
    ) -> None:
        event_id = uuid4().hex

        document = (
            self.client.collection(
                self.COLLECTION_NAME
            )
            .document(event_id)
        )

        document.set(
            {
                "event_id": event_id,
                "event_type": event_type,
                "occurred_at": occurred_at,
                "message": message,
                "data": data,
            }
        )