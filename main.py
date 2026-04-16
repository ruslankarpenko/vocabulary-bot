import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from database.supabase_client import db
from background import keep_alive

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Словник для зберігання станів користувачів (тут, а не в handlers)
user_states = {}

async def main():
    """Головна функція запуску бота"""
    logger.info("🚀 Запуск бота...")
    
    # Ініціалізація бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Ініціалізація Supabase
    db.initialize()
    
    # Імпортуємо роутери тут, щоб уникнути циклічних імпортів
    from handlers.start import router as start_router
    from handlers.modules import router as modules_router
    from handlers.study import router as study_router
    from handlers.library import router as library_router
    from handlers.admin import router as admin_router
    
    # Реєстрація роутерів
    dp.include_router(start_router)
    dp.include_router(modules_router)
    dp.include_router(study_router)
    dp.include_router(library_router)
    dp.include_router(admin_router)
    
    # Запуск веб-сервера для keep-alive
    keep_alive()
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())