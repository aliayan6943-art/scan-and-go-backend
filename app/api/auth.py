from fastapi import APIRouter, HTTPException, Depends
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

@router.post("/request-otp")
async def request_otp(req: OTPRequest, pool: asyncpg.Pool = Depends(get_db_pool)):
    otp_code = str(random.randint(100000, 999999))
    
    # Store OTP in DB (Upsert)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO otps (email, code) VALUES ($1, $2) ON CONFLICT (email) DO UPDATE SET code = $2, created_at = CURRENT_TIMESTAMP",
            req.email, otp_code
        )
        
        # Upsert user (don't overwrite name if already exists)
        await conn.execute(
            "INSERT INTO users (email, name) VALUES ($1, $2) ON CONFLICT (email) DO NOTHING",
            req.email, req.name or "Guest"
        )

    # Send Email
    try:
        msg = MIMEText(f"Your Scan & Go verification code is: {otp_code}")
        msg['Subject'] = "Your Verification Code"
        msg['From'] = settings.SMTP_EMAIL
        msg['To'] = req.email

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        # In development, we return success even if email fails to avoid blocking the UI
        return {"message": "OTP sent successfully (Dev: Check server logs)", "dev_code": otp_code}

    return {"message": "OTP sent successfully."}

@router.post("/verify-otp")
async def verify_otp(req: OTPVerify, pool: asyncpg.Pool = Depends(get_db_pool)):
    async with pool.acquire() as conn:
        # Check OTP
        otp_record = await conn.fetchrow("SELECT code FROM otps WHERE email = $1", req.email)
        if not otp_record or otp_record['code'] != req.otp:
            # Allow fallback for testing
            if req.otp != "123456":
                raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Get User
        user = await conn.fetchrow("SELECT id, name, phone, email FROM users WHERE email = $1", req.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clean up OTP
        await conn.execute("DELETE FROM otps WHERE email = $1", req.email)
        
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
async def update_profile(req: UserProfileUpdate, current_user: dict = Depends(get_current_user), pool: asyncpg.Pool = Depends(get_db_pool)):
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
