from datetime import datetime
from typing import Protocol


class ClassBoardProjector(Protocol):
    def publish(
        self,
        *,
        class_id: int,
        name: str,
        starts_at: datetime,
        capacity: int,
        checked_in: int,
        remaining: int,
        full: bool,
    ) -> None:
        ...