import asyncio
from typing import Optional

class MockRedis:
    def __init__(self):
        self.store = {}
        self.expirations = {}

    async def setex(self, key: str, time: int, value: str):
        self.store[key] = value
        self.expirations[key] = asyncio.get_event_loop().time() + time

    async def get(self, key: str) -> Optional[str]:
        if key in self.store:
            # Check expiration
            if asyncio.get_event_loop().time() > self.expirations.get(key, 0):
                await self.delete(key)
                return None
            return self.store[key]
        return None

    async def delete(self, key: str):
        if key in self.store:
            del self.store[key]
        if key in self.expirations:
            del self.expirations[key]

# Use an in-memory mock so you don't have to configure anything on Railway!
redis_client = MockRedis()

async def get_redis():
    """Dependency to get the redis connection"""
    return redis_client
