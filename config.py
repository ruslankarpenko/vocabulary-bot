import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Завантажуємо .env файл тільки для локальної розробки
if os.path.exists('.env'):
    load_dotenv()

@dataclass
class Config:
    """Конфігурація бота"""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "1533748895"))
    BATCH_SIZE: int = 6
    
    # Мови для фільтрації
    LANGUAGES: List[str] = None
    CLASSES: List[str] = None
    
    def __post_init__(self):
        if self.LANGUAGES is None:
            self.LANGUAGES = [
                "🇬🇧 Англійська",
                "🇺🇦 Українська",
                "🇩🇪 Німецька",
                "🇫🇷 Французька",
                "🇪🇸 Іспанська",
                "🇵🇱 Польська",
                "🇮🇹 Італійська",
                "🇯🇵 Японська"
            ]
        
        if self.CLASSES is None:
            self.CLASSES = [
                "📚 Загальна лексика",
                "💼 Бізнес",
                "✈️ Подорожі",
                "🍽️ Їжа",
                "⚽ Спорт",
                "💻 Технології",
                "🎨 Мистецтво",
                "🔬 Наука",
                "🏥 Медицина",
                "📝 Інше"
            ]

config = Config()
