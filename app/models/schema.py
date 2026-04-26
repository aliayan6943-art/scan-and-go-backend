from pydantic import BaseModel
from typing import List, Optional

class OTPRequest(BaseModel):
    email: str
    name: Optional[str] = None

class OTPVerify(BaseModel):
    email: str
    otp: str

class UserProfileUpdate(BaseModel):
    name: str
    email: str

class CartItemModel(BaseModel):
    barcode: str
    quantity: int

class CheckoutRequest(BaseModel):
    items: List[CartItemModel]

async def create_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS otps (
                email VARCHAR(100) PRIMARY KEY,
                code VARCHAR(6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                barcode VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                image TEXT,
                stock_quantity INT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                total_amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) NOT NULL,
                qr_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transaction_items (
                id SERIAL PRIMARY KEY,
                transaction_id INT REFERENCES transactions(id),
                product_id INT REFERENCES products(id),
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            );
        ''')
        
        # Seed initial products if table is empty
        count = await conn.fetchval("SELECT COUNT(*) FROM products")
        if count == 0:
            products_to_seed = [
                ('8901030940049', 'Premium Ground Coffee', 14.99, 'https://images.unsplash.com/photo-1559525839-b184a4d698c7?w=200&fit=crop', 100),
                ('8901030940050', 'Organic Green Tea', 8.99, 'https://images.unsplash.com/photo-1627435601361-ec2ce5070014?w=200&fit=crop', 50)
            ]
            await conn.executemany(
                "INSERT INTO products (barcode, name, price, image, stock_quantity) VALUES ($1, $2, $3, $4, $5)",
                products_to_seed
            )
            print("Database seeded with initial products.")
            
        print("Database tables ensured.")
