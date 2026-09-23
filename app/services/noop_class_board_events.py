class NoOpClassBoardEventPublisher:
    def publish(
        self,
        payload: dict,
    ) -> None:
        return None