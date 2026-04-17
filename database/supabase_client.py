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
                logger.warning("⚠️ SUPABASE_URL або SUPABASE_KEY не встановлено!")
                return False
                
            logger.info(f"🔗 Підключення до Supabase: {config.SUPABASE_URL}")
            
            # Імпортуємо бібліотеку
            from supabase import create_client
            
            # Пробуємо різні способи
            try:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            except TypeError:
                # Для нових версій
                self.client = create_client(
                    supabase_url=config.SUPABASE_URL,
                    supabase_key=config.SUPABASE_KEY
                )
            except Exception as e:
                # Для старих версій
                import supabase as sb
                self.client = sb.Client(
                    api_url=config.SUPABASE_URL,
                    api_key=config.SUPABASE_KEY
                )
            
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
