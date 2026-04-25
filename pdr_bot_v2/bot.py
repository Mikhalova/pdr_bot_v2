import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import start, tests, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    db.init_db()

    # Завантажуємо питання якщо БД порожня
    if not db.is_db_populated():
        cache = Path("questions.json")
        if cache.exists():
            logger.info("Завантажую питання з questions.json...")
            db.load_from_json(str(cache))
            logger.info("Питання завантажено.")
        else:
            logger.error("questions.json не знайдено! Поклади файл поряд з bot.py")

    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(tests.router)
    dp.include_router(stats.router)

    logger.info("Бот запускається...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
