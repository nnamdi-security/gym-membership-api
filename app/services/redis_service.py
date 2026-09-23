from redis import Redis


class RedisService:
    def __init__(
        self,
        client: Redis,
    ):
        self.client = client

    def ping(self) -> bool:
        return bool(self.client.ping())

    def set_value(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        self.client.set(
            key,
            value,
            ex=ttl_seconds,
        )

    def get_value(
        self,
        key: str,
    ) -> str | None:
        value = self.client.get(key)

        if value is None:
            return None

        return str(value)

    def delete_value(
        self,
        key: str,
    ) -> None:
        self.client.delete(key)
