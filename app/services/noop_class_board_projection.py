class NoOpClassBoardProjector:
    def publish(
        self,
        **kwargs,
    ) -> None:
        return None


    def delete(
        self,
        class_id: int,
    ) -> None:
        return None