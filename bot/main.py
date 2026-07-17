import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import BOT_TOKEN
from bot.handlers.start import router as start_router
from bot.handlers.analysis import router as analysis_router
from bot.handlers.reactions import router as reactions_router
from db.database import init_db, init_metrics_tables

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(analysis_router)
    dp.include_router(reactions_router)

    await init_db()
    await init_metrics_tables()
    logging.info("✅ JDZ Нейропродавец Алекс запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
