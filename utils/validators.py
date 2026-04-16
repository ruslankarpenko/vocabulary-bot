from typing import Tuple, List

def validate_words_input(words_text: str) -> Tuple[bool, List[str], str]:
    """Валідація введення слів"""
    words = [w.strip() for w in words_text.strip().splitlines() if w.strip()]
    
    if not words:
        return False, [], "❌ Введіть хоча б одне слово"
    
    if len(words) > 1000:
        return False, [], "❌ Забагато слів. Максимум 1000 слів за раз"
    
    # Перевірка довжини слів
    for word in words:
        if len(word) > 100:
            return False, [], f"❌ Слово '{word[:50]}...' занадто довге"
    
    return True, words, ""

def validate_module_name(name: str) -> Tuple[bool, str]:
    """Валідація назви модуля"""
    name = name.strip()
    
    if not name:
        return False, "❌ Назва не може бути порожньою"
    
    if len(name) < 3:
        return False, "❌ Назва повинна містити мінімум 3 символи"
    
    if len(name) > 100:
        return False, "❌ Назва занадто довга (максимум 100 символів)"
    
    return True, name