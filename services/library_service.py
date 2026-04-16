import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from database.supabase_client import db
import logging

logger = logging.getLogger(__name__)

class LibraryService:
    """Сервіс для роботи з бібліотекою"""
    
    @staticmethod
    async def create_module_invite(module_id: int, user_id: int, 
                                   expires_days: int = None,
                                   max_uses: int = None) -> Optional[Dict]:
        """Створення посилання-запрошення на модуль"""
        try:
            invite_code = secrets.token_urlsafe(16)
            
            data = {
                "module_id": module_id,
                "invite_code": invite_code,
                "created_by": user_id,
                "max_uses": max_uses
            }
            
            if expires_days:
                data["expires_at"] = (datetime.now() + timedelta(days=expires_days)).isoformat()
            
            result = db.get_client().table("module_invites")\
                .insert(data)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Помилка створення запрошення: {e}")
            return None
    
    @staticmethod
    async def validate_invite(invite_code: str) -> Optional[Dict]:
        """Перевірка валідності запрошення"""
        try:
            result = db.get_client().table("module_invites")\
                .select("*, modules(*)")\
                .eq("invite_code", invite_code)\
                .execute()
            
            if not result.data:
                return None
            
            invite = result.data[0]
            
            # Перевірка терміну дії
            if invite.get("expires_at"):
                expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
                if datetime.now(expires_at.tzinfo) > expires_at:
                    return None
            
            # Перевірка кількості використань
            if invite.get("max_uses") and invite["uses_count"] >= invite["max_uses"]:
                return None
            
            return invite
            
        except Exception as e:
            logger.error(f"Помилка перевірки запрошення: {e}")
            return None
    
    @staticmethod
    async def search_modules(query: str, filters: Dict = None) -> List[Dict]:
        """Пошук модулів"""
        try:
            db_query = db.get_client().table("modules")\
                .select("*")\
                .eq("is_public", True)
            
            if query:
                db_query = db_query.or_(f"name.ilike.%{query}%,description.ilike.%{query}%")
            
            if filters:
                for key, value in filters.items():
                    if value:
                        db_query = db_query.eq(key, value)
            
            result = db_query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Помилка пошуку модулів: {e}")
            return []