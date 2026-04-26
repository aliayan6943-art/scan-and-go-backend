import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def reset_db():
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        await conn.execute('''
            DROP TABLE IF EXISTS transaction_items CASCADE;
            DROP TABLE IF EXISTS transactions CASCADE;
            DROP TABLE IF EXISTS products CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        ''')
        print("Dropped all existing tables successfully.")
        await conn.close()
    except Exception as e:
        print(f"Failed to reset DB: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
