from fastapi import APIRouter, HTTPException, Depends
from app.core.database import get_db_pool
from app.api.deps import get_current_user
import asyncpg

router = APIRouter()

@router.get("/history")
async def get_order_history(
    current_user: dict = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    user_id = int(current_user['sub'])
    
    async with pool.acquire() as conn:
        # STRICT BOUNDARY: Every query MUST include user_id = $1
        orders = await conn.fetch(
            """
            SELECT id, total_amount, status, created_at, qr_token 
            FROM transactions 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            """,
            user_id
        )
        
        result = []
        for order in orders:
            items = await conn.fetch(
                """
                SELECT p.name, ti.quantity, ti.price 
                FROM transaction_items ti
                JOIN products p ON ti.product_id = p.id
                WHERE ti.transaction_id = $1
                """,
                order['id']
            )
            
            order_dict = dict(order)
            order_dict['items'] = [dict(item) for item in items]
            result.append(order_dict)
            
        return result

@router.get("/pending")
async def get_pending_orders(
    current_user: dict = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    user_id = int(current_user['sub'])
    
    async with pool.acquire() as conn:
        # STRICT BOUNDARY: Enforce user_id = $1 to prevent Session Bleed
        pending = await conn.fetch(
            """
            SELECT id, total_amount, status, created_at 
            FROM transactions 
            WHERE user_id = $1 AND status = 'PENDING'
            """,
            user_id
        )
        return [dict(p) for p in pending]
