import logging
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клієнт для роботи з Supabase"""
    
    def __init__(self):
        self.client = None
        self._initialized = False
        
    def initialize(self):
        """Ініціалізація клієнта Supabase"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                logger.error("❌ SUPABASE_URL або SUPABASE_KEY не встановлено!")
                return False
                
            logger.info(f"🔗 Підключення до Supabase: {config.SUPABASE_URL}")
            
            # Видаляємо можливі проблемні змінні оточення
            import os
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                os.environ.pop(key, None)
            
            # Імпортуємо та створюємо клієнт
            from supabase import create_client
            
            self.client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
            
            # Перевіряємо з'єднання простим запитом
            try:
                test = self.client.table("modules").select("id").limit(1).execute()
                logger.info("✅ З'єднання з Supabase перевірено")
            except Exception as e:
                logger.warning(f"⚠️ Не вдалося виконати тестовий запит: {e}")
            
            self._initialized = True
            logger.info("✅ Supabase клієнт ініціалізовано")
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка ініціалізації Supabase: {e}")
            self._initialized = False
            return False
    
    def get_client(self, use_service: bool = False):
        """Отримати клієнт Supabase"""
        if not self._initialized:
            logger.error("❌ Supabase не ініціалізовано!")
            return None
        return self.client

# Глобальний екземпляр
db = SupabaseClient()
