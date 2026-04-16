from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.main import get_main_menu, get_back_to_menu, get_admin_menu
from keyboards.modules import (
    get_modules_keyboard, 
    get_edit_module_actions,
    get_visibility_settings,
    get_study_modes
)
from database.models import ModuleModel, WordsModel, UserLibraryModel
from config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

class ModuleCreation(StatesGroup):
    """Стани для створення модуля"""
    waiting_name = State()
    waiting_description = State()
    waiting_source_lang = State()
    waiting_target_lang = State()
    waiting_category = State()
    waiting_class = State()
    waiting_visibility = State()
    waiting_words = State()
    waiting_translations = State()

class ModuleEditing(StatesGroup):
    """Стани для редагування модуля"""
    waiting_words = State()
    waiting_translations = State()
    waiting_settings = State()

# Імпортуємо user_states з main
from main import user_states

# Додаємо функцію back_to_menu
async def back_to_menu(message: Message):
    """Допоміжна функція повернення в меню"""
    from handlers.start import back_to_menu as start_back_to_menu
    await start_back_to_menu(message)

@router.message(F.text == "📘 Створити набір")
async def create_module_start(message: Message, state: FSMContext):
    """Початок створення нового модуля"""
    await state.set_state(ModuleCreation.waiting_name)
    await message.answer(
        "📝 Введіть назву нового набору слів:",
        reply_markup=get_back_to_menu()
    )

@router.message(ModuleCreation.waiting_name)
async def process_module_name(message: Message, state: FSMContext):
    """Обробка назви модуля"""
    if message.text == "🔙 До меню":
        await state.clear()
        await back_to_menu(message)
        return
    
    await state.update_data(name=message.text.strip())
    await state.set_state(ModuleCreation.waiting_description)
    await message.answer(
        "📄 Введіть опис набору (або натисніть 'Пропустити'):",
        reply_markup=get_back_to_menu()
    )

@router.message(ModuleCreation.waiting_description)
async def process_module_description(message: Message, state: FSMContext):
    """Обробка опису модуля"""
    if message.text == "🔙 До меню":
        await state.clear()
        await back_to_menu(message)
        return
    
    description = None if message.text == "Пропустити" else message.text.strip()
    await state.update_data(description=description)
    
    # Вибір мови оригіналу
    from keyboards.library import get_language_selection_keyboard
    await state.set_state(ModuleCreation.waiting_source_lang)
    await message.answer(
        "🌍 Оберіть мову оригіналу (слів):",
        reply_markup=get_language_selection_keyboard()
    )

@router.callback_query(F.data.startswith("select_lang:"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору мови"""
    current_state = await state.get_state()
    language = callback.data.split(":")[1]
    
    if current_state == ModuleCreation.waiting_source_lang:
        await state.update_data(source_language=language)
        await state.set_state(ModuleCreation.waiting_target_lang)
        await callback.message.edit_text(
            "🌍 Оберіть мову перекладу:",
            reply_markup=callback.message.reply_markup
        )
    elif current_state == ModuleCreation.waiting_target_lang:
        await state.update_data(target_language=language)
        await state.set_state(ModuleCreation.waiting_category)
        
        # Вибір категорії
        from keyboards.library import get_category_selection_keyboard
        await callback.message.edit_text(
            "📂 Оберіть категорію набору:",
            reply_markup=get_category_selection_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("select_category:"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору категорії"""
    category = callback.data.split(":")[1]
    await state.update_data(category=category)
    
    # Вибір класу/рівня
    from keyboards.library import get_class_selection_keyboard
    await state.set_state(ModuleCreation.waiting_class)
    await callback.message.edit_text(
        "📚 Оберіть рівень/клас:",
        reply_markup=get_class_selection_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_class:"))
async def process_class_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору класу"""
    class_name = callback.data.split(":")[1]
    await state.update_data(class_name=class_name)
    
    # Вибір видимості
    await state.set_state(ModuleCreation.waiting_visibility)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔒 Приватний (тільки ви)", callback_data="visibility:private")],
        [InlineKeyboardButton(text="🌍 Публічний (для всіх)", callback_data="visibility:public")],
    ])
    
    await callback.message.edit_text(
        "👁️ Оберіть видимість набору:\n\n"
        "• <b>Приватний</b> - доступний тільки вам\n"
        "• <b>Публічний</b> - з'явиться в публічній бібліотеці",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("visibility:"))
async def process_visibility_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору видимості"""
    visibility = callback.data.split(":")[1]
    is_public = visibility == "public"
    
    await state.update_data(is_public=is_public)
    
    # Створюємо модуль
    data = await state.get_data()
    module = await ModuleModel.create(
        user_id=callback.from_user.id,
        name=data["name"],
        description=data.get("description"),
        is_public=is_public,
        source_lang=data["source_language"],
        target_lang=data["target_language"],
        category=data["category"],
        class_name=data["class_name"]
    )
    
    if module:
        await state.update_data(module_id=module["id"])
        await state.set_state(ModuleCreation.waiting_words)
        
        await callback.message.edit_text(
            f"✅ Набір '{data['name']}' створено!\n\n"
            "Тепер введіть слова (кожне з нового рядка):"
        )
        
        # Надсилаємо звичайне повідомлення для введення слів
        await callback.message.answer(
            "📝 Введіть слова:",
            reply_markup=get_back_to_menu()
        )
    else:
        await callback.message.edit_text(
            "❌ Помилка створення набору. Спробуйте ще раз."
        )
        await state.clear()
    
    await callback.answer()

@router.message(ModuleCreation.waiting_words)
async def process_words_input(message: Message, state: FSMContext):
    """Обробка введення слів"""
    if message.text == "🔙 До меню":
        await state.clear()
        await back_to_menu(message)
        return
    
    words = [w.strip() for w in message.text.strip().splitlines() if w.strip()]
    
    if not words:
        await message.answer("❌ Введіть хоча б одне слово!")
        return
    
    await state.update_data(temp_words=words)
    await state.set_state(ModuleCreation.waiting_translations)
    await message.answer(
        f"📝 Введено {len(words)} слів.\n"
        "Тепер введіть переклади в тому ж порядку (кожен з нового рядка):"
    )

@router.message(ModuleCreation.waiting_translations)
async def process_translations_input(message: Message, state: FSMContext):
    """Обробка введення перекладів та збереження слів"""
    if message.text == "🔙 До меню":
        await state.clear()
        await back_to_menu(message)
        return
    
    translations = [t.strip() for t in message.text.strip().splitlines() if t.strip()]
    data = await state.get_data()
    words = data.get("temp_words", [])
    
    if len(words) != len(translations):
        await message.answer(
            f"❌ Кількість слів ({len(words)}) та перекладів ({len(translations)}) не співпадає.\n"
            "Спробуйте ще раз:"
        )
        return
    
    # Підготовка даних для збереження
    words_data = []
    for i, (word, trans) in enumerate(zip(words, translations)):
        words_data.append({
            "word": word,
            "translation": trans,
            "position": i
        })
    
    # Збереження слів
    success = await WordsModel.add_words(data["module_id"], words_data)
    
    if success:
        await message.answer(
            f"✅ Набір '{data['name']}' успішно створено та заповнено!\n"
            f"📊 Додано слів: {len(words)}",
            reply_markup=get_main_menu() if message.from_user.id != config.ADMIN_ID else get_admin_menu()
        )
    else:
        await message.answer(
            "❌ Помилка при додаванні слів. Спробуйте пізніше.",
            reply_markup=get_main_menu() if message.from_user.id != config.ADMIN_ID else get_admin_menu()
        )
    
    await state.clear()

@router.message(F.text == "✏️ Редагувати набори")
async def edit_modules(message: Message):
    """Показ списку модулів для редагування"""
    user_id = message.from_user.id
    modules = await ModuleModel.get_user_modules(user_id)
    
    if not modules:
        await message.answer(
            "📭 У вас ще немає створених наборів.\n"
            "Створіть перший набір, натиснувши '📘 Створити набір'"
        )
        return
    
    user_states[user_id] = {
        "step": "select_module_to_edit",
        "modules": {m["name"]: m["id"] for m in modules}
    }
    
    await message.answer(
        "📚 Оберіть набір для редагування:",
        reply_markup=get_modules_keyboard(modules)
    )

@router.message(F.text.in_(["🔙 До списку"]))
async def back_to_modules_list(message: Message):
    """Повернення до списку модулів"""
    await edit_modules(message)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "select_module_to_edit")
async def select_module_to_edit(message: Message):
    """Вибір модуля для редагування"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    modules_dict = state.get("modules", {})
    
    module_id = modules_dict.get(message.text)
    if not module_id:
        await message.answer("❌ Оберіть набір зі списку!")
        return
    
    module = await ModuleModel.get_by_id(module_id)
    if not module:
        await message.answer("❌ Набір не знайдено!")
        return
    
    user_states[user_id] = {
        "step": "edit_module_actions",
        "module_id": module_id,
        "module": module
    }
    
    info_text = (
        f"📦 <b>{module['name']}</b>\n"
        f"📝 {module.get('description', 'Без опису')}\n"
        f"🌍 {module.get('source_language', 'Н/Д')} → {module.get('target_language', 'Н/Д')}\n"
        f"👁️ {'🌍 Публічний' if module.get('is_public') else '🔒 Приватний'}\n\n"
        "Оберіть дію:"
    )
    
    await message.answer(info_text, reply_markup=get_edit_module_actions())

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "edit_module_actions")
async def handle_edit_action(message: Message, state: FSMContext):
    """Обробка дій редагування"""
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    module_id = user_state["module_id"]
    module = user_state["module"]
    
    if message.text == "✏️ Редагувати слова":
        # Показуємо поточні слова
        words = await WordsModel.get_module_words(module_id)
        if words:
            words_text = "\n".join([f"{w['word']} - {w['translation']}" for w in words])
            await message.answer(
                f"📝 Поточні слова:\n\n{words_text}\n\n"
                "Введіть нові слова (кожне з нового рядка):"
            )
        else:
            await message.answer("Введіть нові слова (кожне з нового рядка):")
        
        user_states[user_id]["step"] = "editing_words"
        
    elif message.text == "🔄 Поміняти слово/переклад":
        success = await WordsModel.swap_words_translations(module_id)
        if success:
            await message.answer("✅ Слова та переклади успішно поміняні місцями!")
        else:
            await message.answer("❌ Помилка при обміні слів та перекладів")
        
        await edit_modules(message)
        
    elif message.text == "🏷️ Змінити налаштування":
        await state.set_state(ModuleEditing.waiting_settings)
        await state.update_data(module_id=module_id)
        await message.answer(
            "Введіть нові налаштування у форматі:\n"
            "Назва | Опис | Мова оригіналу | Мова перекладу | Категорія | Клас\n\n"
            "Або введіть окремо кожне поле."
        )
        
    elif message.text == "👁️ Налаштування видимості":
        await message.answer(
            f"Поточна видимість: {'🌍 Публічний' if module['is_public'] else '🔒 Приватний'}",
            reply_markup=get_visibility_settings(module['is_public'])
        )
        user_states[user_id]["step"] = "changing_visibility"
        
    elif message.text == "🔗 Створити посилання":
        from services.library_service import LibraryService
        invite = await LibraryService.create_module_invite(module_id, user_id)
        
        if invite:
            bot_username = (await message.bot.me()).username
            invite_link = f"https://t.me/{bot_username}?start=invite_{invite['invite_code']}"
            
            await message.answer(
                f"🔗 Посилання для додавання набору:\n\n"
                f"<code>{invite_link}</code>\n\n"
                f"⏳ Термін дії: {'Безстроково' if not invite.get('expires_at') else invite['expires_at']}\n"
                f"👥 Максимум використань: {invite.get('max_uses', 'Без обмежень')}"
            )
        else:
            await message.answer("❌ Помилка створення посилання")
            
    elif message.text == "🗑️ Видалити набір":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Так, видалити", callback_data=f"delete_module:{module_id}"),
                InlineKeyboardButton(text="❌ Ні, скасувати", callback_data="cancel_delete")
            ]
        ])
        
        await message.answer(
            f"⚠️ Ви впевнені, що хочете видалити набір '{module['name']}'?\n"
            "Цю дію неможливо скасувати!",
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("delete_module:"))
async def confirm_delete_module(callback: CallbackQuery):
    """Підтвердження видалення модуля"""
    module_id = int(callback.data.split(":")[1])
    
    success = await ModuleModel.delete(module_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text("✅ Набір успішно видалено!")
    else:
        await callback.message.edit_text("❌ Помилка видалення набору")
    
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    """Скасування видалення"""
    await callback.message.edit_text("❌ Видалення скасовано")
    await callback.answer()

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "changing_visibility")
async def handle_visibility_change(message: Message):
    """Зміна видимості модуля"""
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    module_id = user_state["module_id"]
    module = user_state["module"]
    
    if message.text == "🔄 Змінити видимість":
        new_visibility = not module["is_public"]
        success = await ModuleModel.update(
            module_id, 
            user_id, 
            {"is_public": new_visibility}
        )
        
        if success:
            module["is_public"] = new_visibility
            user_states[user_id]["module"] = module
            
            await message.answer(
                f"✅ Видимість змінено на: {'🌍 Публічний' if new_visibility else '🔒 Приватний'}",
                reply_markup=get_visibility_settings(new_visibility)
            )
        else:
            await message.answer("❌ Помилка зміни видимості")
            
    elif message.text == "🔙 Назад":
        user_states[user_id]["step"] = "edit_module_actions"
        await message.answer(
            "Оберіть дію:",
            reply_markup=get_edit_module_actions()
        )