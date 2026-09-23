class NoOpClassBoardEventPublisher:
    def publish(
        self,
        payload: dict,
    ) -> None:
        return None

    def delete(
        self,
        class_id: int,
    ) -> None:
        return None