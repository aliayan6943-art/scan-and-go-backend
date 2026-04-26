import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

products = [
    ('8901262000012', 'Amul Milk 500ml', 28.00, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200&fit=crop', 100),
    ('8901058001123', 'Maggi 2-Minute Noodles', 14.00, 'https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=200&fit=crop', 200),
    ('8901719123456', 'Parle-G Biscuits (250g)', 35.00, 'https://images.unsplash.com/photo-1590080875515-ce84f74dd726?w=200&fit=crop', 150),
    ('8904006301234', 'Tata Salt (1kg)', 28.00, 'https://images.unsplash.com/photo-1626015469490-9f17d23a1f33?w=200&fit=crop', 120),
    ('8901491105678', 'Lay’s Classic Chips (52g)', 20.00, 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=200&fit=crop', 80),
    ('8901764032109', 'Coca-Cola 750ml', 40.00, 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200&fit=crop', 90)
]

async def seed_db():
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        # Ensure tables exist
        from app.models.schema import create_tables
        # We need a pool for create_tables, but we can mock it or just use the connection
        # Actually create_tables expects a pool. Let's use asyncpg.create_pool instead.
        await conn.close()
        pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        await create_tables(pool)
        
        conn = await pool.acquire()
        
        # Check if products already exist and insert if not
        for product in products:
            exists = await conn.fetchval("SELECT id FROM products WHERE barcode = $1", product[0])
            if not exists:
                await conn.execute(
                    "INSERT INTO products (barcode, name, price, image, stock_quantity) VALUES ($1, $2, $3, $4, $5)",
                    product[0], product[1], product[2], product[3], product[4]
                )
                print(f"Added {product[1]}")
            else:
                # Update price if it exists
                await conn.execute(
                    "UPDATE products SET price = $1, name = $2 WHERE barcode = $3",
                    product[2], product[1], product[0]
                )
                print(f"Updated {product[1]}")
                
        await pool.release(conn)
        await pool.close()
        print("Database seeding completed.")
    except Exception as e:
        print(f"Failed to seed DB: {e}")

if __name__ == "__main__":
    asyncio.run(seed_db())
