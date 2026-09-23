from app.core.redis import get_redis
from app.services.redis_service import RedisService


def test_real_redis_connection():
    service = RedisService(
        get_redis()
    )

    assert service.ping() is True