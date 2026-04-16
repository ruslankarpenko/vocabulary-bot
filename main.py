import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask
from threading import Thread

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app для health check
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Імпорт конфігурації
from config import config
from database.supabase_client import db

# Словник для зберігання станів користувачів
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
    try:
        db.initialize()
        logger.info("✅ Supabase ініціалізовано")
    except Exception as e:
        logger.error(f"❌ Помилка ініціалізації Supabase: {e}")
    
    # Імпортуємо роутери
    try:
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
        
        logger.info("✅ Роутери зареєстровано")
    except Exception as e:
        logger.error(f"❌ Помилка реєстрації роутерів: {e}")
    
    # Запускаємо Flask в окремому потоці
    Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask сервер запущено для health checks")
    
    # Запуск бота
    try:
        logger.info("🤖 Бот запущено!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Помилка запуску бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
