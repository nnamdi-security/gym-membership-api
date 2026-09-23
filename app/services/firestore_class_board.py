from google.cloud import firestore

from app.core.config import settings


class FirestoreClassBoardProjector:
    COLLECTION_NAME = "class_boards"

    def __init__(self):
        self.client = firestore.Client(
            project=settings.firestore_project_id,
        )

    def publish(
        self,
        *,
        class_id: int,
        name: str,
        starts_at,
        capacity: int,
        checked_in: int,
        remaining: int,
        full: bool,
    ) -> None:
        document = (
            self.client.collection(
                self.COLLECTION_NAME
            )
            .document(str(class_id))
        )

        document.set(
            {
                "class_id": class_id,
                "name": name,
                "starts_at": starts_at,
                "capacity": capacity,
                "checked_in": checked_in,
                "remaining": remaining,
                "full": full,
            }
        )