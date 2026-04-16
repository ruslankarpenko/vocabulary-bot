from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору мови"""
    builder = InlineKeyboardBuilder()
    
    for lang in config.LANGUAGES:
        builder.button(
            text=lang,
            callback_data=f"select_lang:{lang}"
        )
    
    builder.adjust(2)
    return builder.as_markup()

def get_category_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору категорії"""
    builder = InlineKeyboardBuilder()
    
    for category in config.CLASSES:
        builder.button(
            text=category,
            callback_data=f"select_category:{category}"
        )
    
    builder.adjust(2)
    return builder.as_markup()

def get_class_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору класу/рівня"""
    classes = [
        "🟢 Початковий (A1)",
        "🟡 Базовий (A2)",
        "🟠 Середній (B1)",
        "🔵 Вище середнього (B2)",
        "🟣 Просунутий (C1)",
        "🔴 Професійний (C2)"
    ]
    
    builder = InlineKeyboardBuilder()
    
    for class_name in classes:
        builder.button(
            text=class_name,
            callback_data=f"select_class:{class_name}"
        )
    
    builder.adjust(1)
    return builder.as_markup()