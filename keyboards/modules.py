from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict

def get_modules_keyboard(modules: List[Dict], action: str = "select") -> ReplyKeyboardMarkup:
    """Клавіатура зі списком модулів"""
    builder = ReplyKeyboardBuilder()
    
    for module in modules:
        builder.button(text=module["name"])
    
    builder.button(text="🔙 До меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_edit_module_actions() -> ReplyKeyboardMarkup:
    """Дії для редагування модуля"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="✏️ Редагувати слова")
    builder.button(text="🔄 Поміняти слово/переклад")
    builder.button(text="🏷️ Змінити налаштування")
    builder.button(text="👁️ Налаштування видимості")
    builder.button(text="🔗 Створити посилання")
    builder.button(text="🗑️ Видалити набір")
    builder.button(text="🔙 До списку")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_visibility_settings(is_public: bool) -> ReplyKeyboardMarkup:
    """Налаштування видимості модуля"""
    builder = ReplyKeyboardBuilder()
    
    status = "✅" if is_public else "❌"
    builder.button(text=f"{status} Публічний: {'Так' if is_public else 'Ні'}")
    builder.button(text="🔄 Змінити видимість")
    builder.button(text="🔙 Назад")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_study_modes() -> ReplyKeyboardMarkup:
    """Режими вивчення"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Картки")
    builder.button(text="✅ Тест: Правильно/Неправильно")
    builder.button(text="🔢 Тест: 4 варіанти")
    builder.button(text="⌨️ Введення перекладу")
    builder.button(text="🧠 Режим заучування")
    builder.button(text="🔙 До вибору набору")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_language_filter_keyboard(current_filter: Dict = None) -> InlineKeyboardMarkup:
    """Клавіатура для фільтрації за мовами"""
    from config import config
    
    builder = InlineKeyboardBuilder()
    
    for lang in config.LANGUAGES[:6]:  # Показуємо перші 6 мов
        builder.button(
            text=f"{lang} {'✓' if current_filter and current_filter.get('language') == lang else ''}",
            callback_data=f"filter_lang:{lang}"
        )
    
    builder.button(text="📚 Всі категорії", callback_data="filter_category")
    builder.button(text="🔍 Скинути фільтри", callback_data="filter_reset")
    builder.button(text="✅ Застосувати", callback_data="filter_apply")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()

def get_category_filter_keyboard(current_filter: Dict = None) -> InlineKeyboardMarkup:
    """Клавіатура для фільтрації за категоріями"""
    from config import config
    
    builder = InlineKeyboardBuilder()
    
    for category in config.CLASSES[:8]:  # Показуємо перші 8 категорій
        builder.button(
            text=f"{category} {'✓' if current_filter and current_filter.get('class') == category else ''}",
            callback_data=f"filter_class:{category}"
        )
    
    builder.button(text="🔙 Назад до мов", callback_data="filter_back_to_lang")
    builder.button(text="🔍 Скинути фільтри", callback_data="filter_reset")
    builder.adjust(1)
    return builder.as_markup()