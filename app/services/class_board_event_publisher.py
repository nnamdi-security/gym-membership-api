from typing import Protocol


class ClassBoardEventPublisher(Protocol):
    def publish(
        self,
        payload: dict,
    ) -> None:
        ...