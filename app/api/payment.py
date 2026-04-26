from fastapi import APIRouter, HTTPException, Depends, Request, Header
import razorpay
from app.core.config import settings
from app.core.database import get_db_pool
from app.api.deps import get_current_user
import asyncpg
import json

from pydantic import BaseModel

router = APIRouter()

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class PaymentRequest(BaseModel):
    amount: float

@router.post("/create-order")
async def create_order(req: PaymentRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Amount in paise
        data = {
            "amount": int(req.amount * 100),
            "currency": "INR",
            "receipt": f"receipt_{current_user['sub']}",
            "payment_capture": 1
        }
        order = client.order.create(data=data)
        return {"order_id": order['id'], "amount": data['amount'], "key": settings.RAZORPAY_KEY_ID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    body = await request.body()
    
    try:
        # Verify Webhook Signature
        client.utility.verify_webhook_signature(
            body.decode(),
            x_razorpay_signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
        
        event_data = json.loads(body)
        event = event_data.get("event")
        
        if event == "order.paid":
            order_id = event_data['payload']['payment']['entity']['order_id']
            # Update status in DB
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE transactions SET status = 'completed' WHERE qr_token = $1",
                    order_id # Using order_id as token for simplicity in this phase
                )
        
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
