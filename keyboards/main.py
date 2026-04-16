from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    """Головне меню"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📘 Створити набір")
    builder.button(text="✏️ Редагувати набори")
    builder.button(text="📚 Вчити слова")
    builder.button(text="📖 Публічна бібліотека")
    builder.button(text="📊 Моя статистика")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню адміністратора"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📢 Розсилка")
    builder.button(text="📊 Статистика бота")
    builder.button(text="👥 Користувачі")
    builder.button(text="📚 Керування бібліотекою")
    builder.button(text="🔙 Головне меню")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_menu() -> ReplyKeyboardMarkup:
    """Кнопка повернення в меню"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 До меню")
    return builder.as_markup(resize_keyboard=True)