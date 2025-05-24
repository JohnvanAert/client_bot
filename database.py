import asyncpg
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import os
# Настройки подключения к БД
load_dotenv()

DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'host': os.getenv('DB_HOST')
}

# Пул соединений
pool: asyncpg.Pool = None

# Подключение к базе данных
async def connect_db():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)


# Добавление нового заказчика
async def add_customer(telegram_id: int, full_name: str, iin_or_bin: str, phone: str, email: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO customers (telegram_id, full_name, iin_or_bin, phone, email)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (telegram_id) DO UPDATE 
            SET full_name = EXCLUDED.full_name,
                iin_or_bin = EXCLUDED.iin_or_bin,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email
        """, telegram_id, full_name, iin_or_bin, phone, email)

# Получение информации о заказчике
async def get_customer_by_telegram_id(telegram_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM customers WHERE telegram_id = $1", telegram_id)
        return dict(row) if row else None

# Получение всех заказов
async def add_order(title: str, description: str, document_url: str, customer_id: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO orders (title, description, document_url, customer_id, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, title, description, document_url, customer_id)


# Получение заказчика по Telegram ID
async def get_customer_by_telegram_id(telegram_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM customers WHERE telegram_id = $1
        """, telegram_id)
        return dict(row) if row else None

# Получить всех ГИПов
async def get_all_gips():
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id FROM users WHERE role = 'гип'")
        return [row["telegram_id"] for row in rows]
