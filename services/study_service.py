import random
from typing import List, Dict, Optional
from database.models import WordsModel, UserProgressModel

class StudyService:
    """Сервіс для роботи з вивченням слів"""
    
    @staticmethod
    async def get_words_to_study(user_id: int, module_id: int, 
                                 include_learned: bool = False) -> List[Dict]:
        """Отримати слова для вивчення"""
        all_words = await WordsModel.get_module_words(module_id)
        
        if include_learned:
            return all_words
        
        learned_ids = await UserProgressModel.get_learned_words(user_id, module_id)
        return [w for w in all_words if w["id"] not in learned_ids]
    
    @staticmethod
    def generate_test_options(correct_answer: str, all_words: List[Dict], 
                              options_count: int = 4) -> List[str]:
        """Генерація варіантів для тесту"""
        options = [correct_answer]
        
        # Беремо інші переклади
        other_translations = [
            w["translation"] for w in all_words 
            if w["translation"] != correct_answer
        ]
        
        # Випадково вибираємо варіанти
        random.shuffle(other_translations)
        options.extend(other_translations[:options_count - 1])
        
        # Якщо недостатньо варіантів, дублюємо правильний
        while len(options) < options_count:
            options.append(correct_answer)
        
        random.shuffle(options)
        return options
    
    @staticmethod
    def calculate_accuracy(correct: int, total: int) -> float:
        """Розрахунок точності"""
        return (correct / total * 100) if total > 0 else 0.0
    
    @staticmethod
    async def get_module_progress(user_id: int, module_id: int) -> Dict:
        """Отримати прогрес по модулю"""
        total_words = len(await WordsModel.get_module_words(module_id))
        learned_words = len(await UserProgressModel.get_learned_words(user_id, module_id))
        
        return {
            "total": total_words,
            "learned": learned_words,
            "remaining": total_words - learned_words,
            "percentage": (learned_words / total_words * 100) if total_words > 0 else 0
        }