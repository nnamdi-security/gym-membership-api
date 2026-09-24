from datetime import datetime
from typing import Protocol


class ActivityFeedProjector(Protocol):
    def publish(
        self,
        *,
        event_type: str,
        occurred_at: datetime,
        message: str,
        data: dict,
    ) -> None: ...
