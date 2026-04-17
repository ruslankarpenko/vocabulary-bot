from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.main import get_admin_menu
from database.models import BroadcastModel, ModuleModel
from database.supabase_client import db
from config import config
import logging
import asyncio

logger = logging.getLogger(__name__)
router = Router()

class BroadcastStates(StatesGroup):
    """Стани для створення розсилки"""
    waiting_message = State()
    waiting_image = State()
    waiting_button = State()
    waiting_confirmation = State()

@router.message(F.text == "📢 Розсилка")
async def start_broadcast(message: Message, state: FSMContext):
    """Початок створення розсилки"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас немає прав для цієї дії.")
        return
    
    await state.set_state(BroadcastStates.waiting_message)
    await message.answer(
        "📢 <b>Створення розсилки</b>\n\n"
        "Введіть текст повідомлення для розсилки:\n"
        "<i>Підтримується HTML-форматування</i>"
    )

@router.message(BroadcastStates.waiting_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обробка тексту розсилки"""
    if message.text == "🔙 Головне меню":
        await state.clear()
        await message.answer("Головне меню:", reply_markup=get_admin_menu())
        return
    
    await state.update_data(message_text=message.text)
    await state.set_state(BroadcastStates.waiting_image)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустити", callback_data="skip_image")
    builder.button(text="❌ Скасувати", callback_data="cancel_broadcast")
    
    await message.answer(
        "🖼️ Надішліть зображення для розсилки (або натисніть 'Пропустити'):",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "skip_image")
async def skip_broadcast_image(callback: CallbackQuery, state: FSMContext):
    """Пропуск додавання зображення"""
    await state.update_data(image_url=None)
    await state.set_state(BroadcastStates.waiting_button)
    
    await callback.message.delete()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустити", callback_data="skip_button")
    builder.button(text="❌ Скасувати", callback_data="cancel_broadcast")
    
    await callback.message.answer(
        "🔘 Бажаєте додати кнопку?\n\n"
        "Введіть дані у форматі:\n"
        "<code>Текст кнопки | URL</code>\n\n"
        "Або натисніть 'Пропустити'",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.message(BroadcastStates.waiting_image, F.photo)
async def process_broadcast_image(message: Message, state: FSMContext):
    """Обробка зображення для розсилки"""
    # Отримуємо file_id найбільшого зображення
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await state.update_data(image_url=file_id)
    await state.set_state(BroadcastStates.waiting_button)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустити", callback_data="skip_button")
    builder.button(text="❌ Скасувати", callback_data="cancel_broadcast")
    
    await message.answer(
        "✅ Зображення додано!\n\n"
        "🔘 Бажаєте додати кнопку?\n"
        "Введіть дані у форматі:\n"
        "<code>Текст кнопки | URL</code>\n\n"
        "Або натисніть 'Пропустити'",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "skip_button")
async def skip_broadcast_button(callback: CallbackQuery, state: FSMContext):
    """Пропуск додавання кнопки"""
    await state.update_data(button_text=None, button_url=None)
    await state.set_state(BroadcastStates.waiting_confirmation)
    
    data = await state.get_data()
    
    await callback.message.delete()
    await show_broadcast_preview(callback.message, data)

@router.message(BroadcastStates.waiting_button)
async def process_broadcast_button(message: Message, state: FSMContext):
    """Обробка даних кнопки"""
    try:
        parts = message.text.split("|")
        if len(parts) != 2:
            raise ValueError("Неправильний формат")
        
        button_text = parts[0].strip()
        button_url = parts[1].strip()
        
        if not button_text or not button_url:
            raise ValueError("Пусті значення")
        
        await state.update_data(
            button_text=button_text,
            button_url=button_url
        )
        
        await state.set_state(BroadcastStates.waiting_confirmation)
        
        data = await state.get_data()
        await show_broadcast_preview(message, data)
        
    except Exception as e:
        await message.answer(
            "❌ Неправильний формат. Введіть дані у форматі:\n"
            "<code>Текст кнопки | URL</code>"
        )

async def show_broadcast_preview(message: Message, data: dict):
    """Показ прев'ю розсилки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Відправити", callback_data="confirm_broadcast")
    builder.button(text="✏️ Редагувати", callback_data="edit_broadcast")
    builder.button(text="❌ Скасувати", callback_data="cancel_broadcast")
    builder.adjust(1)
    
    preview_text = (
        "📋 <b>Прев'ю розсилки</b>\n\n"
        f"📝 <b>Текст:</b>\n{data['message_text']}\n\n"
        f"🖼️ <b>Зображення:</b> {'✅' if data.get('image_url') else '❌'}\n"
        f"🔘 <b>Кнопка:</b> {'✅' if data.get('button_text') else '❌'}\n"
    )
    
    if data.get('button_text'):
        preview_text += f"\n🔗 {data['button_text']} → {data['button_url']}"
    
    preview_text += "\n\nПідтвердіть відправку:"
    
    # Відправляємо прев'ю
    if data.get('image_url'):
        await message.answer_photo(
            photo=data['image_url'],
            caption=preview_text,
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Підтвердження та відправка розсилки"""
    data = await state.get_data()
    admin_id = callback.from_user.id
    
    # Видаляємо попереднє повідомлення
    await callback.message.delete()
    
    # Відправляємо нове повідомлення про початок розсилки
    status_msg = await callback.message.answer("📤 <b>Починаю розсилку...</b>\nБудь ласка, зачекайте.")
    
    # Отримуємо всіх користувачів
    users = await BroadcastModel.get_all_users()
    
    # Створюємо запис про розсилку
    broadcast = await BroadcastModel.create_broadcast(
        admin_id=admin_id,
        message_text=data['message_text'],
        image_url=data.get('image_url'),
        button_text=data.get('button_text'),
        button_url=data.get('button_url')
    )
    
    # Відправляємо повідомлення
    success_count = 0
    fail_count = 0
    
    for user_id in users:
        try:
            # Створюємо клавіатуру якщо є кнопка
            reply_markup = None
            if data.get('button_text') and data.get('button_url'):
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=data['button_text'],
                        url=data['button_url']
                    )
                ]])
                reply_markup = keyboard
            
            # Відправляємо повідомлення
            if data.get('image_url'):
                await callback.bot.send_photo(
                    chat_id=user_id,
                    photo=data['image_url'],
                    caption=data['message_text'],
                    reply_markup=reply_markup
                )
            else:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=data['message_text'],
                    reply_markup=reply_markup
                )
            
            success_count += 1
            await asyncio.sleep(0.05)  # Затримка для уникнення обмежень
            
        except Exception as e:
            logger.error(f"Помилка відправки користувачу {user_id}: {e}")
            fail_count += 1
    
    # Оновлюємо статистику
    if broadcast:
        try:
            client = db.get_client(use_service=True)
            if client:
                client.table("broadcasts")\
                    .update({"recipients_count": success_count})\
                    .eq("id", broadcast["id"])\
                    .execute()
        except Exception as e:
            logger.error(f"Помилка оновлення статистики: {e}")
    
    # Редагуємо статусне повідомлення
    await status_msg.edit_text(
        f"✅ <b>Розсилку завершено!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✅ Успішно: {success_count}\n"
        f"❌ Помилок: {fail_count}\n"
        f"📈 Всього користувачів: {len(users)}"
    )
    
    await state.clear()
    await callback.answer("Розсилку завершено!")

@router.callback_query(F.data == "edit_broadcast")
async def edit_broadcast(callback: CallbackQuery, state: FSMContext):
    """Редагування розсилки"""
    await state.set_state(BroadcastStates.waiting_message)
    await callback.message.edit_text(
        "✏️ Введіть новий текст повідомлення:"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Скасування розсилки"""
    await state.clear()
    await callback.message.edit_text("❌ Розсилку скасовано")
    await callback.message.answer("Головне меню:", reply_markup=get_admin_menu())
    await callback.answer()

@router.message(F.text == "📊 Статистика бота")
async def show_bot_statistics(message: Message):
    """Показ статистики бота"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас немає прав для цієї дії.")
        return
    
    # Отримуємо статистику
    users = await BroadcastModel.get_all_users()
    total_users = len(users)
    
    # Кількість модулів
    modules_result = db.get_client(use_service=True).table("modules")\
        .select("id, is_public")\
        .execute()
    
    total_modules = len(modules_result.data)
    public_modules = len([m for m in modules_result.data if m.get("is_public")])
    
    # Кількість слів
    words_result = db.get_client(use_service=True).table("words")\
        .select("id")\
        .execute()
    total_words = len(words_result.data)
    
    # Статистика розсилок
    broadcasts_result = db.get_client(use_service=True).table("broadcasts")\
        .select("*")\
        .order("sent_at", desc=True)\
        .limit(5)\
        .execute()
    
    stats_text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 <b>Користувачі:</b>\n"
        f"• Всього користувачів: {total_users}\n\n"
        f"📚 <b>Набори слів:</b>\n"
        f"• Всього наборів: {total_modules}\n"
        f"• Публічних наборів: {public_modules}\n"
        f"• Приватних наборів: {total_modules - public_modules}\n\n"
        f"📝 <b>Слова:</b>\n"
        f"• Всього слів: {total_words}\n"
        f"• Середнє слів у наборі: {total_words / total_modules if total_modules > 0 else 0:.1f}\n\n"
        f"📢 <b>Останні розсилки:</b>\n"
    )
    
    for broadcast in broadcasts_result.data[:3]:
        stats_text += (
            f"• {broadcast['sent_at'][:10]}: "
            f"{broadcast['recipients_count']} отримувачів\n"
        )
    
    await message.answer(stats_text)

@router.message(F.text == "👥 Користувачі")
async def show_users_list(message: Message):
    """Показ списку користувачів"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас немає прав для цієї дії.")
        return
    
    users = await BroadcastModel.get_all_users()
    
    # Групуємо користувачів по активності
    users_with_modules = set()
    users_with_progress = set()
    
    modules_result = db.get_client(use_service=True).table("modules")\
        .select("user_id")\
        .execute()
    users_with_modules.update(item["user_id"] for item in modules_result.data)
    
    progress_result = db.get_client(use_service=True).table("user_progress")\
        .select("user_id")\
        .execute()
    users_with_progress.update(item["user_id"] for item in progress_result.data)
    
    stats_text = (
        f"👥 <b>Статистика користувачів</b>\n\n"
        f"📊 Всього користувачів: {len(users)}\n"
        f"📚 Створили набори: {len(users_with_modules)}\n"
        f"📝 Почали вивчення: {len(users_with_progress)}\n"
    )
    
    # Показуємо топ активних користувачів
    user_activity = {}
    for user_id in users:
        # Рахуємо активність
        modules_count = len([m for m in modules_result.data if m["user_id"] == user_id])
        progress_count = len([p for p in progress_result.data if p["user_id"] == user_id])
        user_activity[user_id] = modules_count + progress_count
    
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if top_users:
        stats_text += "\n🏆 <b>Топ активних користувачів:</b>\n"
        for i, (user_id, activity) in enumerate(top_users, 1):
            stats_text += f"{i}. ID {user_id}: {activity} дій\n"
    
    await message.answer(stats_text)

@router.message(F.text == "📚 Керування бібліотекою")
async def manage_library(message: Message):
    """Керування публічною бібліотекою"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас немає прав для цієї дії.")
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика бібліотеки", callback_data="admin_library_stats")
    builder.button(text="🔍 Переглянути всі набори", callback_data="admin_view_all_modules")
    builder.button(text="🗑️ Видалити набір", callback_data="admin_delete_module")
    builder.button(text="✏️ Редагувати набір", callback_data="admin_edit_module")
    builder.adjust(1)
    
    await message.answer(
        "📚 <b>Керування бібліотекою</b>\n\n"
        "Оберіть дію:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_library_stats")
async def admin_library_stats(callback: CallbackQuery):
    """Статистика бібліотеки для адміна"""
    # Отримуємо детальну статистику
    modules_result = db.get_client(use_service=True).table("modules")\
        .select("*")\
        .eq("is_public", True)\
        .execute()
    
    public_modules = modules_result.data
    
    # Статистика по мовах
    languages = {}
    categories = {}
    
    for module in public_modules:
        source_lang = module.get("source_language", "Н/Д")
        category = module.get("category", "Н/Д")
        
        languages[source_lang] = languages.get(source_lang, 0) + 1
        categories[category] = categories.get(category, 0) + 1
    
    stats_text = (
        f"📊 <b>Статистика публічної бібліотеки</b>\n\n"
        f"📚 Всього публічних наборів: {len(public_modules)}\n\n"
    )
    
    if languages:
        stats_text += "<b>🌍 По мовах:</b>\n"
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"• {lang}: {count}\n"
    
    if categories:
        stats_text += "\n<b>📂 По категоріях:</b>\n"
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"• {cat}: {count}\n"
    
    await callback.message.edit_text(stats_text)
    await callback.answer()

# Імпорт функції back_to_menu з start.py
from handlers.start import back_to_menu
