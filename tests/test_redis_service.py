from app.services.redis_service import RedisService


class FakeRedis:
    def __init__(self):
        self.values: dict[str, str] = {}

    def ping(self):
        return True

    def set(
        self,
        key,
        value,
        ex=None,
    ):
        self.values[key] = value

    def get(
        self,
        key,
    ):
        return self.values.get(key)

    def delete(
        self,
        key,
    ):
        self.values.pop(
            key,
            None,
        )


def test_redis_service_ping():
    service = RedisService(
        FakeRedis()
    )

    assert service.ping() is True


def test_redis_service_set_and_get():
    service = RedisService(
        FakeRedis()
    )

    service.set_value(
        "test:key",
        "hello",
    )

    assert (
        service.get_value("test:key")
        == "hello"
    )


def test_redis_service_delete():
    service = RedisService(
        FakeRedis()
    )

    service.set_value(
        "test:key",
        "hello",
    )

    service.delete_value(
        "test:key"
    )

    assert (
        service.get_value("test:key")
        is None
    )