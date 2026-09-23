from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)

async_redis_client = AsyncRedis.from_url(
    settings.redis_url,
    decode_responses=True,
)
# decode_responses=True means Redis gives us normal Python strings rather than raw bytes for text values.


def get_redis() -> Redis:
    return redis_client


def get_async_redis() -> AsyncRedis:
    return async_redis_client
