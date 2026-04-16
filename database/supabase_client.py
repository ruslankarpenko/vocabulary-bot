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
        
    def initialize(self):
        """Ініціалізація клієнтів Supabase"""
        try:
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
            
            logger.info("✅ Supabase клієнти ініціалізовано")
        except Exception as e:
            logger.error(f"❌ Помилка ініціалізації Supabase: {e}")
            raise
    
    def get_client(self, use_service: bool = False) -> Client:
        """Отримати клієнт Supabase"""
        if use_service and self.service_client:
            return self.service_client
        return self.client

# Глобальний екземпляр
db = SupabaseClient()