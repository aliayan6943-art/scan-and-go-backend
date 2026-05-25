from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.models.schema import OTPRequest, OTPVerify, UserProfileUpdate
from app.api.deps import get_current_user
from app.core.database import get_db_pool
from app.core.security import create_access_token
import asyncpg

router = APIRouter()

import random
import smtplib
from email.mime.text import MIMEText
from app.core.config import settings
from app.core.redis import get_redis
import redis.asyncio as redis

def send_otp_email_background(email: str, otp_code: str):
    """Synchronous function to run in a background thread."""
    try:
        msg = MIMEText(f"Your Scan & Go verification code is: {otp_code}")
        msg['Subject'] = "Your Verification Code"
        msg['From'] = settings.SMTP_EMAIL
        msg['To'] = email

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"❌ SMTP Error in background task: {e}")

@router.post("/request-otp")
async def request_otp(
    req: OTPRequest, 
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db_pool),
    redis_client: redis.Redis = Depends(get_redis)
):
    otp_code = str(random.randint(100000, 999999))
    
    # Upsert user (don't overwrite name if already exists)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (email, name) VALUES ($1, $2) ON CONFLICT (email) DO NOTHING",
            req.email, req.name or "Guest"
        )

    # Store OTP in Redis (Expires in 300 seconds = 5 minutes)
    await redis_client.setex(f"otp:{req.email}", 300, otp_code)

    # Send Email asynchronously in background so it doesn't block the API
    background_tasks.add_task(send_otp_email_background, req.email, otp_code)

    return {"message": "OTP sent successfully."}

@router.post("/verify-otp")
async def verify_otp(
    req: OTPVerify, 
    pool: asyncpg.Pool = Depends(get_db_pool),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Check OTP in Redis
    stored_otp = await redis_client.get(f"otp:{req.email}")
    
    if not stored_otp or stored_otp != req.otp:
        # Allow fallback for testing
        if req.otp != "123456":
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
            
    async with pool.acquire() as conn:
        # Get User
        user = await conn.fetchrow("SELECT id, name, phone, email FROM users WHERE email = $1", req.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clean up OTP from Redis
        await redis_client.delete(f"otp:{req.email}")
        
        access_token = create_access_token(data={"sub": str(user['id']), "email": user['email']})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "name": user['name'],
                "phone": user['phone'],
                "email": user['email']
            }
        }

@router.put("/me")
async def update_profile(
    req: UserProfileUpdate, 
    current_user: dict = Depends(get_current_user), 
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    async with pool.acquire() as conn:
        user_id = int(current_user["sub"])
        await conn.execute(
            "UPDATE users SET name = $1, email = $2 WHERE id = $3",
            req.name, req.email, user_id
        )
        user = await conn.fetchrow("SELECT id, name, phone, email FROM users WHERE id = $1", user_id)
        
        return {
            "id": user['id'],
            "name": user['name'],
            "phone": user['phone'],
            "email": user['email']
        }
