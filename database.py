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

async def update_order_document(order_id: int, new_path: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE orders
            SET document_url = $1
            WHERE id = $2
        """, new_path, order_id)

async def get_order_by_customer_id(customer_telegram_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT o.*
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE u.telegram_id = $1
            ORDER BY o.created_at DESC
            LIMIT 1
        """, customer_telegram_id)
        return dict(row) if row else None


async def get_orders_by_customer_telegram(telegram_id: int):
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT o.id, o.title, o.status
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE c.telegram_id = $1
            ORDER BY o.created_at DESC
        """, telegram_id)


async def get_order_by_id(order_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
        return dict(row) if row else None


# Получить специалиста по разделу
async def get_specialist_by_section(section: str):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT id, telegram_id FROM users
            WHERE role = 'специалист' AND section = $1
            LIMIT 1
        """, section)


async def update_order_status(order_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE orders SET status = $1 WHERE id = $2",
            status, order_id
        )


async def get_order_pending_fix_by_customer(customer_telegram_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT o.*
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE u.telegram_id = $1 AND o.status = 'pending_correction'
            LIMIT 1
        """, customer_telegram_id)


