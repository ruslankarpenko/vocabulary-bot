from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing import List

def get_flashcard_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для режиму карток"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="👁️ Показати переклад")
    builder.button(text="🔙 До меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_know_dont_know_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура Знаю/Не знаю"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Знаю")
    builder.button(text="❌ Не знаю")
    builder.button(text="🔙 До меню")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_choice_test_keyboard(options: List[str]) -> ReplyKeyboardMarkup:
    """Клавіатура для тесту з варіантами"""
    builder = ReplyKeyboardBuilder()
    for option in options:
        builder.button(text=option)
    builder.button(text="🔙 До меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_writing_test_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для письмового тесту"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Не знаю")
    builder.button(text="🔙 До меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_true_false_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура Правильно/Неправильно"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Правильно")
    builder.button(text="❌ Неправильно")
    builder.button(text="🔙 До меню")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)