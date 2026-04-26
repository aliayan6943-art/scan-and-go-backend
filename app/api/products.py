from fastapi import APIRouter, HTTPException, Depends
from app.core.database import get_db_pool
import asyncpg

router = APIRouter()

@router.get("/{barcode}")
async def get_product(barcode: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    async with pool.acquire() as conn:
        product = await conn.fetchrow(
            "SELECT id, barcode, name, price, image, stock_quantity FROM products WHERE barcode = $1", 
            barcode
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(product)
