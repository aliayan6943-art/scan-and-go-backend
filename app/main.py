from fastapi import FastAPI
from app.core.database import db
from app.api import auth, products, checkout, payment, orders
from app.models.schema import create_tables

app = FastAPI(title="Smart Retail API")

@app.on_event("startup")
async def startup_event():
    await db.connect()
    pool = db.pool
    await create_tables(pool)

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
app.include_router(payment.router, prefix="/payment", tags=["payment"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Retail API"}
