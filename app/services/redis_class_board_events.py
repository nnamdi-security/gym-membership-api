import json

from redis import Redis

from app.core.channels import CLASS_BOARD_CHANNEL


class RedisClassBoardEventPublisher:
    def __init__(
        self,
        client: Redis,
    ):
        self.client = client

    def publish(
        self,
        payload: dict,
    ) -> None:
        self.client.publish(
            CLASS_BOARD_CHANNEL,
            json.dumps(
                payload,
                default=str,
            ),
        )