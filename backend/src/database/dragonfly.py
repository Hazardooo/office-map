from typing import AsyncGenerator
import redis.asyncio as redis
from redis.asyncio import Redis

from src.settings import settings
from src.database.exceptions import DragonflyUnavailable


async def get_dragonfly() -> AsyncGenerator[Redis, None]:
    try:
        async with redis.from_url(
                settings.DRAGONFLY_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=1,
                max_connections=50,
        ) as conn:
            yield conn

    except Exception:
        print("Dragonfly unavailable")
        raise DragonflyUnavailable()