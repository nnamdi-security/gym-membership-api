import asyncio

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from starlette.responses import StreamingResponse

from app.api.dependencies.auth import get_current_user
from app.core.channels import CLASS_BOARD_CHANNEL
from app.core.redis import get_async_redis


router = APIRouter(
    prefix="/live",
    tags=["Live"],
)


CURRENT_USER_DEPENDENCY = Depends(
    get_current_user
)


async def class_board_event_stream(
    request: Request,
    redis_client: Redis,
):
    pubsub = redis_client.pubsub()

    await pubsub.subscribe(
        CLASS_BOARD_CHANNEL
    )

    try:
        while True:
            if await request.is_disconnected():
                break

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message is not None:
                data = message["data"]

                yield (
                    "event: class-board\n"
                    f"data: {data}\n\n"
                )

            else:
                yield ": keep-alive\n\n"

            await asyncio.sleep(0.1)

    finally:
        await pubsub.unsubscribe(
            CLASS_BOARD_CHANNEL
        )
        await pubsub.aclose()



@router.get(
    "/class-board",
    summary="Stream live class-board updates",
    dependencies=[CURRENT_USER_DEPENDENCY],
)
async def stream_class_board(
    request: Request,
):
    return StreamingResponse(
        class_board_event_stream(
            request,
            get_async_redis(),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )