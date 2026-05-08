import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

BLACKLIST_PREFIX = "token_blacklist:"


async def add_to_blacklist(jti: str, expires_in: int) -> None:
    """Add token to blacklist."""
    await redis_client.setex(f"{BLACKLIST_PREFIX}{jti}", expires_in, "1")


async def is_blacklisted(jti: str) -> bool:
    """Check if token is blacklisted."""
    return await redis_client.exists(f"{BLACKLIST_PREFIX}{jti}") > 0
