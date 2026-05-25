import redis.asyncio as redis
from app.core.config import settings

# Global Redis connection pool
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    """Dependency to get the redis connection"""
    return redis_client
