import asyncio
import asyncpg
import os
import random
from dotenv import load_dotenv

load_dotenv()

async def test_auth():
    print("Connecting to DB...")
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        email = "test@example.com"
        name = "Test User"
        otp_code = "123456"
        
        print(f"Testing UPSERT for {email}...")
        
        # 1. Test OTP Upsert
        await conn.execute(
            "INSERT INTO otps (email, code) VALUES ($1, $2) ON CONFLICT (email) DO UPDATE SET code = $2, created_at = CURRENT_TIMESTAMP",
            email, otp_code
        )
        print("OTP Upsert: Success")
        
        # 2. Test User Upsert
        # Check if email exists
        res = await conn.execute(
            "INSERT INTO users (email, name) VALUES ($1, $2) ON CONFLICT (email) DO NOTHING",
            email, name
        )
        print(f"User Upsert: Success ({res})")
        
        print("All local DB operations for auth request succeeded!")
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_auth())
