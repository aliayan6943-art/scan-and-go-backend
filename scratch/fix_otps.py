import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        print("Dropping and recreating 'otps' table...")
        await conn.execute("DROP TABLE IF EXISTS otps")
        await conn.execute('''
            CREATE TABLE otps (
                email VARCHAR(100) PRIMARY KEY,
                code VARCHAR(6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
