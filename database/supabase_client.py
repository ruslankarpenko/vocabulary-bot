from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from config import config

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клієнт для роботи з Supabase"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.service_client: Optional[Client] = None
        self._initialized = False
        
    def initialize(self):
        """Ініціалізація клієнтів Supabase"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                logger.error("❌ SUPABASE_URL або SUPABASE_KEY не встановлено!")
                return False
                
            self.client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
            
            # Сервісний клієнт для адмін-операцій
            if config.SUPABASE_SERVICE_KEY:
                self.service_client = create_client(
                    config.SUPABASE_URL,
                    config.SUPABASE_SERVICE_KEY
                )
            
            self._initialized = True
            logger.info("✅ Supabase клієнти ініціалізовано")
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка ініціалізації Supabase: {e}")
            self._initialized = False
            return False
    
    def get_client(self, use_service: bool = False) -> Optional[Client]:
        """Отримати клієнт Supabase"""
        if not self._initialized:
            logger.error("❌ Supabase не ініціалізовано!")
            return None
            
        if use_service and self.service_client:
            return self.service_client
        return self.client

# Глобальний екземпляр
db = SupabaseClient()
