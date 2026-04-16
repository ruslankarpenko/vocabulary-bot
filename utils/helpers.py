from typing import List, Dict

def format_module_info(module: Dict, words_count: int = None) -> str:
    """Форматування інформації про модуль"""
    info = [
        f"📦 <b>{module.get('name', 'Без назви')}</b>",
        f"📝 {module.get('description', 'Без опису')}",
        f"🌍 {module.get('source_language', 'Н/Д')} → {module.get('target_language', 'Н/Д')}",
        f"📂 {module.get('category', 'Н/Д')}",
        f"👁️ {'🌍 Публічний' if module.get('is_public') else '🔒 Приватний'}"
    ]
    
    if words_count is not None:
        info.append(f"📊 Слів: {words_count}")
    
    return "\n".join(info)

def format_word_list(words: List[Dict], limit: int = None) -> str:
    """Форматування списку слів"""
    if not words:
        return "📭 Список порожній"
    
    if limit:
        words = words[:limit]
        suffix = f"\n... і ще {len(words) - limit}" if len(words) > limit else ""
    else:
        suffix = ""
    
    formatted = "\n".join([f"• {w['word']} - {w['translation']}" for w in words])
    return formatted + suffix

def generate_progress_bar(percentage: float, length: int = 10) -> str:
    """Генерація прогрес-бару"""
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"