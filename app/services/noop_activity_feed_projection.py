class NoOpActivityFeedProjector:
    def publish(
        self,
        **kwargs,
    ) -> None:
        return None