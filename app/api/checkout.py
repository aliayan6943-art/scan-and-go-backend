from fastapi import APIRouter, HTTPException, Depends
from app.models.schema import CheckoutRequest
from app.core.database import get_db_pool
from app.api.deps import get_current_user
from app.core.config import settings
import asyncpg
import hmac
import hashlib
import json
import time

router = APIRouter()

def generate_qr_token(transaction_id: int, user_id: int) -> str:
    payload = {
        "tx_id": transaction_id,
        "u_id": user_id,
        "ts": int(time.time())
    }
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_str}.{signature}"

@router.post("/")
async def process_checkout(
    req: CheckoutRequest, 
    user: dict = Depends(get_current_user), 
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    user_id = int(user['sub'])
    
    async with pool.acquire() as conn:
        # Start a database transaction
        async with conn.transaction():
            total_amount = 0.0
            processed_items = []
            
            # Sort barcodes to avoid deadlocks when locking multiple rows
            sorted_items = sorted(req.items, key=lambda x: x.barcode)
            
            for item in sorted_items:
                # SELECT ... FOR UPDATE to lock the row and prevent race conditions
                product = await conn.fetchrow(
                    "SELECT id, price, stock_quantity, name FROM products WHERE barcode = $1 FOR UPDATE",
                    item.barcode
                )
                
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product with barcode {item.barcode} not found")
                
                if product['stock_quantity'] < item.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Insufficient stock for {product['name']}. Available: {product['stock_quantity']}"
                    )
                
                # Deduct stock
                await conn.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - $1 WHERE id = $2",
                    item.quantity, product['id']
                )
                
                item_total = float(product['price']) * item.quantity
                total_amount += item_total
                
                processed_items.append({
                    "product_id": product['id'],
                    "quantity": item.quantity,
                    "price": product['price']
                })
                
            # Create transaction record
            tx_id = await conn.fetchval(
                "INSERT INTO transactions (user_id, total_amount, status) VALUES ($1, $2, $3) RETURNING id",
                user_id, total_amount, "COMPLETED"
            )
            
            # Insert transaction items
            for p_item in processed_items:
                await conn.execute(
                    "INSERT INTO transaction_items (transaction_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)",
                    tx_id, p_item['product_id'], p_item['quantity'], p_item['price']
                )
                
            # Generate secure HMAC token
            qr_token = generate_qr_token(tx_id, user_id)
            
            # Update transaction with the token
            await conn.execute(
                "UPDATE transactions SET qr_token = $1 WHERE id = $2",
                qr_token, tx_id
            )
            
    return {
        "message": "Checkout successful",
        "transaction_id": tx_id,
        "total_amount": total_amount,
        "qr_token": qr_token
    }
