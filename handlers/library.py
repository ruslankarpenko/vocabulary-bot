from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.main import get_main_menu, get_admin_menu
from keyboards.modules import get_language_filter_keyboard, get_category_filter_keyboard
from database.models import ModuleModel, WordsModel, UserLibraryModel
from services.library_service import LibraryService
from config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

# Імпортуємо user_states з main
from main import user_states

@router.message(F.text == "📖 Публічна бібліотека")
async def show_public_library(message: Message):
    """Показ публічної бібліотеки"""
    user_id = message.from_user.id
    
    user_states[user_id] = {
        "step": "browsing_library",
        "filters": {}
    }
    
    await show_filtered_modules(message, user_id)

async def show_filtered_modules(message: Message, user_id: int, page: int = 0):
    """Показ відфільтрованих модулів"""
    state = user_states.get(user_id, {})
    filters = state.get("filters", {})
    
    modules = await ModuleModel.get_public_modules(filters)
    
    if not modules:
        await message.answer(
            "📭 У публічній бібліотеці поки немає наборів з такими фільтрами.\n"
            "Спробуйте змінити фільтри або створіть свій набір!",
            reply_markup=get_main_menu() if user_id != config.ADMIN_ID else get_admin_menu()
        )
        return
    
    # Пагінація
    items_per_page = 5
    total_pages = (len(modules) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_modules = modules[start_idx:end_idx]
    
    # Створюємо інлайн клавіатуру з модулями
    builder = InlineKeyboardBuilder()
    
    for module in current_modules:
        # Отримуємо кількість слів
        words = await WordsModel.get_module_words(module["id"])
        words_count = len(words)
        
        # Перевіряємо чи вже в бібліотеці користувача
        library_modules = await UserLibraryModel.get_user_library(user_id)
        is_added = any(m["id"] == module["id"] for m in library_modules)
        
        status = "✅" if is_added else "➕"
        
        builder.button(
            text=f"{status} {module['name']} ({words_count} слів)",
            callback_data=f"view_module:{module['id']}"
        )
    
    # Додаємо кнопки навігації
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"lib_page:{page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text="🔍 Фільтри", 
        callback_data="show_filters"
    ))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Вперед", 
            callback_data=f"lib_page:{page+1}"
        ))
    
    builder.row(*nav_buttons)
    builder.adjust(1)
    
    # Додаємо кнопку повернення
    builder.row(InlineKeyboardButton(
        text="🔙 До меню", 
        callback_data="back_to_menu"
    ))
    
    filter_text = ""
    if filters:
        filter_parts = []
        if filters.get("source_language"):
            filter_parts.append(f"🌍 {filters['source_language']}")
        if filters.get("target_language"):
            filter_parts.append(f"➡️ {filters['target_language']}")
        if filters.get("category"):
            filter_parts.append(f"📂 {filters['category']}")
        if filters.get("class"):
            filter_parts.append(f"📚 {filters['class']}")
        
        if filter_parts:
            filter_text = "\n".join(filter_parts) + "\n\n"
    
    await message.answer(
        f"📖 <b>Публічна бібліотека</b>\n\n"
        f"{filter_text}"
        f"📄 Сторінка {page + 1}/{total_pages}\n"
        f"📚 Всього наборів: {len(modules)}\n\n"
        "Оберіть набір для перегляду:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("lib_page:"))
async def handle_library_pagination(callback: CallbackQuery):
    """Обробка пагінації в бібліотеці"""
    page = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    await callback.message.delete()
    await show_filtered_modules(callback.message, user_id, page)
    await callback.answer()

@router.callback_query(F.data == "show_filters")
async def show_filter_menu(callback: CallbackQuery):
    """Показ меню фільтрів"""
    user_id = callback.from_user.id
    state = user_states.get(user_id, {})
    filters = state.get("filters", {})
    
    await callback.message.edit_text(
        "🔍 <b>Фільтри пошуку</b>\n\n"
        "Оберіть мову оригіналу:",
        reply_markup=get_language_filter_keyboard(filters)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filter_lang:"))
async def set_language_filter(callback: CallbackQuery):
    """Встановлення фільтру мови"""
    language = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    if "filters" not in user_states[user_id]:
        user_states[user_id]["filters"] = {}
    
    user_states[user_id]["filters"]["source_language"] = language
    
    await callback.message.edit_text(
        f"✅ Вибрано мову: {language}\n\n"
        "Тепер оберіть категорію:",
        reply_markup=get_category_filter_keyboard(user_states[user_id]["filters"])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filter_class:"))
async def set_class_filter(callback: CallbackQuery):
    """Встановлення фільтру класу"""
    class_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    if "filters" not in user_states[user_id]:
        user_states[user_id]["filters"] = {}
    
    user_states[user_id]["filters"]["class"] = class_name
    
    # Показуємо поточні фільтри
    filters = user_states[user_id]["filters"]
    filter_text = "\n".join([f"• {k}: {v}" for k, v in filters.items()])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Застосувати фільтри", callback_data="filter_apply")
    builder.button(text="🔄 Скинути фільтри", callback_data="filter_reset")
    builder.button(text="📖 Показати всі", callback_data="filter_show_all")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📋 <b>Поточні фільтри:</b>\n\n{filter_text}\n\n"
        "Оберіть дію:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "filter_back_to_lang")
async def back_to_language_filter(callback: CallbackQuery):
    """Повернення до вибору мови"""
    user_id = callback.from_user.id
    state = user_states.get(user_id, {})
    filters = state.get("filters", {})
    
    await callback.message.edit_text(
        "🔍 <b>Фільтри пошуку</b>\n\n"
        "Оберіть мову оригіналу:",
        reply_markup=get_language_filter_keyboard(filters)
    )
    await callback.answer()

@router.callback_query(F.data == "filter_reset")
async def reset_filters(callback: CallbackQuery):
    """Скидання фільтрів"""
    user_id = callback.from_user.id
    user_states[user_id]["filters"] = {}
    
    await callback.message.delete()
    await show_filtered_modules(callback.message, user_id, 0)
    await callback.answer("🔄 Фільтри скинуто")

@router.callback_query(F.data == "filter_apply")
async def apply_filters(callback: CallbackQuery):
    """Застосування фільтрів"""
    user_id = callback.from_user.id
    
    await callback.message.delete()
    await show_filtered_modules(callback.message, user_id, 0)
    await callback.answer("✅ Фільтри застосовано")

@router.callback_query(F.data == "filter_show_all")
async def show_all_modules(callback: CallbackQuery):
    """Показ всіх модулів без фільтрів"""
    user_id = callback.from_user.id
    user_states[user_id]["filters"] = {}
    
    await callback.message.delete()
    await show_filtered_modules(callback.message, user_id, 0)
    await callback.answer()

@router.callback_query(F.data.startswith("view_module:"))
async def view_module_details(callback: CallbackQuery):
    """Перегляд деталей модуля"""
    module_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    module = await ModuleModel.get_by_id(module_id)
    if not module:
        await callback.answer("❌ Модуль не знайдено", show_alert=True)
        return
    
    words = await WordsModel.get_module_words(module_id)
    
    # Перевіряємо чи модуль вже в бібліотеці
    library_modules = await UserLibraryModel.get_user_library(user_id)
    is_added = any(m["id"] == module_id for m in library_modules)
    
    # Створюємо клавіатуру
    builder = InlineKeyboardBuilder()
    
    if not is_added:
        builder.button(
            text="➕ Додати до моєї бібліотеки",
            callback_data=f"add_to_library:{module_id}"
        )
    else:
        builder.button(
            text="✅ Вже у вашій бібліотеці",
            callback_data="already_added"
        )
    
    builder.button(
        text="📚 Почати вивчення",
        callback_data=f"study_module:{module_id}"
    )
    
    # Показуємо тільки перші 5 слів
    words_preview = "\n".join([
        f"• {w['word']} - {w['translation']}" 
        for w in words[:5]
    ])
    
    if len(words) > 5:
        words_preview += f"\n... і ще {len(words) - 5} слів"
    
    info_text = (
        f"📦 <b>{module['name']}</b>\n\n"
        f"📝 {module.get('description', 'Без опису')}\n\n"
        f"🌍 Мови: {module.get('source_language', 'Н/Д')} → {module.get('target_language', 'Н/Д')}\n"
        f"📂 Категорія: {module.get('category', 'Н/Д')}\n"
        f"📚 Рівень: {module.get('class', 'Н/Д')}\n"
        f"📊 Кількість слів: {len(words)}\n\n"
        f"<b>Перші слова:</b>\n{words_preview}"
    )
    
    builder.button(text="🔙 До бібліотеки", callback_data="back_to_library")
    builder.adjust(1)
    
    await callback.message.edit_text(
        info_text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("add_to_library:"))
async def add_to_library(callback: CallbackQuery):
    """Додавання модуля до бібліотеки користувача"""
    module_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    success = await UserLibraryModel.add_module(user_id, module_id)
    
    if success:
        await callback.answer("✅ Набір додано до вашої бібліотеки!", show_alert=True)
        
        # Оновлюємо повідомлення
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Вже у вашій бібліотеці",
            callback_data="already_added"
        )
        builder.button(
            text="📚 Почати вивчення",
            callback_data=f"study_module:{module_id}"
        )
        builder.button(text="🔙 До бібліотеки", callback_data="back_to_library")
        builder.adjust(1)
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    else:
        await callback.answer("❌ Помилка додавання до бібліотеки", show_alert=True)

@router.callback_query(F.data == "already_added")
async def already_added(callback: CallbackQuery):
    """Модуль вже додано"""
    await callback.answer("ℹ️ Цей набір вже у вашій бібліотеці", show_alert=True)

@router.callback_query(F.data.startswith("study_module:"))
async def study_from_library(callback: CallbackQuery):
    """Початок вивчення модуля з бібліотеки"""
    module_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    module = await ModuleModel.get_by_id(module_id)
    if not module:
        await callback.answer("❌ Модуль не знайдено", show_alert=True)
        return
    
    # Ініціалізуємо стан для вивчення
    from handlers.study import start_study_mode
    
    user_states[user_id] = {
        "step": "choose_study_mode",
        "module_id": module_id,
        "module": module
    }
    
    await callback.message.delete()
    
    # Отримуємо статистику
    total_words = len(await WordsModel.get_module_words(module_id))
    learned_words = len(await UserProgressModel.get_learned_words(user_id, module_id))
    
    from keyboards.modules import get_study_modes
    
    stats_text = (
        f"📦 <b>{module['name']}</b>\n"
        f"📊 Прогрес: {learned_words}/{total_words} слів вивчено\n"
        f"📈 Відсоток: {(learned_words/total_words*100 if total_words > 0 else 0):.1f}%\n\n"
        "Оберіть режим вивчення:"
    )
    
    await callback.message.answer(stats_text, reply_markup=get_study_modes())
    await callback.answer()

@router.callback_query(F.data == "back_to_library")
async def back_to_library(callback: CallbackQuery):
    """Повернення до бібліотеки"""
    user_id = callback.from_user.id
    
    await callback.message.delete()
    await show_filtered_modules(callback.message, user_id, 0)
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    """Повернення до головного меню"""
    user_id = callback.from_user.id
    user_states[user_id] = {}
    
    await callback.message.delete()
    
    if user_id == config.ADMIN_ID:
        await callback.message.answer("Головне меню:", reply_markup=get_admin_menu())
    else:
        await callback.message.answer("Головне меню:", reply_markup=get_main_menu())
    
    await callback.answer()

# Обробник для посилань-запрошень
@router.message(F.text.startswith("/start invite_"))
async def handle_invite_link(message: Message):
    """Обробка посилання-запрошення"""
    invite_code = message.text.replace("/start invite_", "").strip()
    user_id = message.from_user.id
    
    # Отримуємо інформацію про запрошення
    from database.supabase_client import db
    
    try:
        result = db.get_client().table("module_invites")\
            .select("*, modules(*)")\
            .eq("invite_code", invite_code)\
            .execute()
        
        if not result.data:
            await message.answer(
                "❌ Посилання недійсне або застаріле.",
                reply_markup=get_main_menu()
            )
            return
        
        invite = result.data[0]
        module = invite["modules"]
        
        # Перевіряємо термін дії
        from datetime import datetime
        if invite.get("expires_at"):
            expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
            if datetime.now(expires_at.tzinfo) > expires_at:
                await message.answer(
                    "❌ Термін дії посилання закінчився.",
                    reply_markup=get_main_menu()
                )
                return
        
        # Перевіряємо кількість використань
        if invite.get("max_uses") and invite["uses_count"] >= invite["max_uses"]:
            await message.answer(
                "❌ Досягнуто максимальної кількості використань посилання.",
                reply_markup=get_main_menu()
            )
            return
        
        # Додаємо модуль до бібліотеки
        success = await UserLibraryModel.add_module(user_id, module["id"])
        
        if success:
            # Збільшуємо лічильник використань
            db.get_client().table("module_invites")\
                .update({"uses_count": invite["uses_count"] + 1})\
                .eq("id", invite["id"])\
                .execute()
            
            await message.answer(
                f"✅ Набір '{module['name']}' успішно додано до вашої бібліотеки!\n\n"
                f"📝 {module.get('description', '')}\n"
                f"📊 Слів у наборі: {len(await WordsModel.get_module_words(module['id']))}\n\n"
                "Можете почати вивчення в розділі '📚 Вчити слова'",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "❌ Помилка додавання набору. Можливо, він вже у вашій бібліотеці.",
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Помилка обробки запрошення: {e}")
        await message.answer(
            "❌ Виникла помилка. Спробуйте пізніше.",
            reply_markup=get_main_menu()
        )