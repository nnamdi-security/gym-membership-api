from redis import Redis

from app.core.config import settings


redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)
# decode_responses=True means Redis gives us normal Python strings rather than raw bytes for text values.


def get_redis() -> Redis:
    return redis_client