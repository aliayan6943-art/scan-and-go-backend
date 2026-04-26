import asyncpg
from typing import Optional
from app.core.config import settings

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )
            print("Database connection pool established")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise e

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Database connection pool closed")

db = Database()

async def get_db_pool() -> asyncpg.Pool:
    if not db.pool:
        await db.connect()
    return db.pool
