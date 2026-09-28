#This Provide the same interface as the real activity-feed projector which writes activity events to Firestore, but intentionally do nothing
class NoOpActivityFeedProjector:
    def publish(
        self,
        **kwargs,
    ) -> None:
        return None
