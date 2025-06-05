# clientbot/bot.py
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import registration
from database import connect_db
from dotenv import load_dotenv
import os
from handlers import order
from handlers import my_orders
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

# Bot and Dispatcher setup
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(registration.router)
dp.include_router(order.router)
dp.include_router(my_orders.router)
async def main():
    await connect_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
