import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import BOT_TOKEN
from bot.handlers.start import router as start_router
from bot.handlers.analysis import router as analysis_router
from db.database import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(analysis_router)

    await init_db()
    logging.info("✅ JDZ Нейропродавец Алекс запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
