from app.core.config import settings
from app.core.redis import get_redis
from app.services.noop_class_board_events import (
    NoOpClassBoardEventPublisher,
)
from app.services.redis_class_board_events import (
    RedisClassBoardEventPublisher,
)


def get_class_board_event_publisher():
    if settings.app_env == "test":
        return NoOpClassBoardEventPublisher()

    return RedisClassBoardEventPublisher(
        get_redis()
    )