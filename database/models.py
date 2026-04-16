from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from .supabase_client import db

logger = logging.getLogger(__name__)

class ModuleModel:
    """Модель для роботи з модулями"""
    
    @staticmethod
    async def create(user_id: int, name: str, description: str = None, 
                     is_public: bool = False, source_lang: str = None, 
                     target_lang: str = None, category: str = None, 
                     class_name: str = None) -> Optional[Dict]:
        """Створення нового модуля"""
        try:
            client = db.get_client()
            if not client:
                logger.error("❌ Клієнт Supabase не доступний")
                return None
                
            data = {
                "user_id": user_id,
                "name": name,
                "description": description,
                "is_public": is_public,
                "source_language": source_lang,
                "target_language": target_lang,
                "category": category,
                "class": class_name
            }
            
            # Видаляємо None значення
            data = {k: v for k, v in data.items() if v is not None}
            
            result = client.table("modules").insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Помилка створення модуля: {e}")
            return None
    
    @staticmethod
    async def get_user_modules(user_id: int) -> List[Dict]:
        """Отримати модулі користувача"""
        try:
            client = db.get_client()
            if not client:
                return []
                
            result = client.table("modules")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Помилка отримання модулів: {e}")
            return []
    
    @staticmethod
    async def get_public_modules(filters: Dict = None) -> List[Dict]:
        """Отримати публічні модулі з фільтрацією"""
        try:
            client = db.get_client()
            if not client:
                return []
                
            query = client.table("modules")\
                .select("*")\
                .eq("is_public", True)\
                .order("created_at", desc=True)
            
            if filters:
                if filters.get("source_language"):
                    query = query.eq("source_language", filters["source_language"])
                if filters.get("target_language"):
                    query = query.eq("target_language", filters["target_language"])
                if filters.get("category"):
                    query = query.eq("category", filters["category"])
                if filters.get("class"):
                    query = query.eq("class", filters["class"])
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Помилка отримання публічних модулів: {e}")
            return []
    
    @staticmethod
    async def get_by_id(module_id: int) -> Optional[Dict]:
        """Отримати модуль за ID"""
        try:
            client = db.get_client()
            if not client:
                return None
                
            result = client.table("modules")\
                .select("*")\
                .eq("id", module_id)\
                .execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Помилка отримання модуля: {e}")
            return None
    
    @staticmethod
    async def update(module_id: int, user_id: int, data: Dict) -> bool:
        """Оновити модуль"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            result = client.table("modules")\
                .update(data)\
                .eq("id", module_id)\
                .eq("user_id", user_id)\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка оновлення модуля: {e}")
            return False
    
    @staticmethod
    async def delete(module_id: int, user_id: int) -> bool:
        """Видалити модуль"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            result = client.table("modules")\
                .delete()\
                .eq("id", module_id)\
                .eq("user_id", user_id)\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка видалення модуля: {e}")
            return False


class WordsModel:
    """Модель для роботи зі словами"""
    
    @staticmethod
    async def add_words(module_id: int, words_data: List[Dict]) -> bool:
        """Додати слова до модуля"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            for word_data in words_data:
                word_data["module_id"] = module_id
            
            result = client.table("words").insert(words_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка додавання слів: {e}")
            return False
    
    @staticmethod
    async def get_module_words(module_id: int) -> List[Dict]:
        """Отримати всі слова модуля"""
        try:
            client = db.get_client()
            if not client:
                return []
                
            result = client.table("words")\
                .select("*")\
                .eq("module_id", module_id)\
                .order("id")\
                .execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Помилка отримання слів: {e}")
            return []
    
    @staticmethod
    async def delete_all_words(module_id: int) -> bool:
        """Видалити всі слова модуля"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            result = client.table("words")\
                .delete()\
                .eq("module_id", module_id)\
                .execute()
            return True
            
        except Exception as e:
            logger.error(f"Помилка видалення слів: {e}")
            return False
    
    @staticmethod
    async def swap_words_translations(module_id: int) -> bool:
        """Поміняти місцями слова та переклади"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            words = await WordsModel.get_module_words(module_id)
            
            for word in words:
                client.table("words")\
                    .update({
                        "word": word["translation"],
                        "translation": word["word"]
                    })\
                    .eq("id", word["id"])\
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка обміну слів та перекладів: {e}")
            return False


class UserProgressModel:
    """Модель для роботи з прогресом користувача"""
    
    @staticmethod
    async def update_word_status(user_id: int, module_id: int, 
                                 word_id: int, status: str) -> bool:
        """Оновити статус слова"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            data = {
                "user_id": user_id,
                "module_id": module_id,
                "word_id": word_id,
                "status": status,
                "last_reviewed": datetime.now().isoformat(),
                "review_count": 1
            }
            
            result = client.table("user_progress")\
                .upsert(data, on_conflict="user_id,module_id,word_id")\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка оновлення прогресу: {e}")
            return False
    
    @staticmethod
    async def get_learned_words(user_id: int, module_id: int) -> List[int]:
        """Отримати ID вивчених слів"""
        try:
            client = db.get_client()
            if not client:
                return []
                
            result = client.table("user_progress")\
                .select("word_id")\
                .eq("user_id", user_id)\
                .eq("module_id", module_id)\
                .eq("status", "learned")\
                .execute()
            return [item["word_id"] for item in result.data] if result.data else []
            
        except Exception as e:
            logger.error(f"Помилка отримання вивчених слів: {e}")
            return []
    
    @staticmethod
    async def reset_module_progress(user_id: int, module_id: int) -> bool:
        """Скинути прогрес по модулю"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            result = client.table("user_progress")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("module_id", module_id)\
                .execute()
            return True
            
        except Exception as e:
            logger.error(f"Помилка скидання прогресу: {e}")
            return False


class LearningProgressModel:
    """Модель для роботи з прогресом навчання"""
    
    @staticmethod
    async def save_progress(user_id: int, module_id: int, 
                           current_batch: int, current_word_index: int) -> bool:
        """Зберегти прогрес навчання"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            data = {
                "user_id": user_id,
                "module_id": module_id,
                "current_batch": current_batch,
                "current_word_index": current_word_index
            }
            
            result = client.table("learning_progress")\
                .upsert(data, on_conflict="user_id,module_id")\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка збереження прогресу навчання: {e}")
            return False
    
    @staticmethod
    async def get_progress(user_id: int, module_id: int) -> Optional[Dict]:
        """Отримати прогрес навчання"""
        try:
            client = db.get_client()
            if not client:
                return None
                
            result = client.table("learning_progress")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("module_id", module_id)\
                .execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Помилка отримання прогресу навчання: {e}")
            return None


class UserLibraryModel:
    """Модель для роботи з бібліотекою користувача"""
    
    @staticmethod
    async def add_module(user_id: int, module_id: int) -> bool:
        """Додати модуль до бібліотеки"""
        try:
            client = db.get_client()
            if not client:
                return False
                
            data = {
                "user_id": user_id,
                "module_id": module_id
            }
            
            result = client.table("user_library")\
                .upsert(data, on_conflict="user_id,module_id")\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Помилка додавання до бібліотеки: {e}")
            return False
    
    @staticmethod
    async def get_user_library(user_id: int) -> List[Dict]:
        """Отримати бібліотеку користувача"""
        try:
            client = db.get_client()
            if not client:
                return []
                
            result = client.table("user_library")\
                .select("module_id, modules(*)")\
                .eq("user_id", user_id)\
                .execute()
            return [item["modules"] for item in result.data if item.get("modules")] if result.data else []
            
        except Exception as e:
            logger.error(f"Помилка отримання бібліотеки: {e}")
            return []
