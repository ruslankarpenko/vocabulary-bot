from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.main import get_main_menu, get_admin_menu
from keyboards.modules import get_modules_keyboard, get_study_modes
from keyboards.study import (
    get_flashcard_keyboard,
    get_choice_test_keyboard,
    get_writing_test_keyboard,
    get_know_dont_know_keyboard
)
from database.models import (
    ModuleModel, 
    WordsModel, 
    UserProgressModel,
    LearningProgressModel,
    UserLibraryModel
)
from services.study_service import StudyService
from config import config
import logging
import random

logger = logging.getLogger(__name__)
router = Router()

# Імпортуємо user_states з main
from main import user_states

# Додаємо функцію back_to_menu
async def back_to_menu(message: Message):
    """Допоміжна функція повернення в меню"""
    from handlers.start import back_to_menu as start_back_to_menu
    await start_back_to_menu(message)

@router.message(F.text == "📚 Вчити слова")
async def choose_module_to_study(message: Message):
    """Вибір модуля для вивчення"""
    user_id = message.from_user.id
    
    # Отримуємо модулі користувача
    own_modules = await ModuleModel.get_user_modules(user_id)
    
    # Отримуємо модулі з бібліотеки
    library_modules = await UserLibraryModel.get_user_library(user_id)
    
    # Об'єднуємо списки
    all_modules = own_modules + library_modules
    
    if not all_modules:
        await message.answer(
            "📭 У вас ще немає наборів для вивчення.\n"
            "Створіть власний набір або додайте з публічної бібліотеки!"
        )
        return
    
    user_states[user_id] = {
        "step": "choose_study_module",
        "modules": {m["name"]: m["id"] for m in all_modules}
    }
    
    await message.answer(
        "📚 Оберіть набір для вивчення:",
        reply_markup=get_modules_keyboard(all_modules)
    )

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "choose_study_module")
async def select_study_module(message: Message):
    """Обробка вибору модуля для вивчення"""
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
    
    # Отримуємо статистику по модулю
    total_words = len(await WordsModel.get_module_words(module_id))
    learned_words = len(await UserProgressModel.get_learned_words(user_id, module_id))
    
    user_states[user_id] = {
        "step": "choose_study_mode",
        "module_id": module_id,
        "module": module
    }
    
    stats_text = (
        f"📦 <b>{module['name']}</b>\n"
        f"📊 Прогрес: {learned_words}/{total_words} слів вивчено\n"
        f"📈 Відсоток: {(learned_words/total_words*100 if total_words > 0 else 0):.1f}%\n\n"
        "Оберіть режим вивчення:"
    )
    
    await message.answer(stats_text, reply_markup=get_study_modes())

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "choose_study_mode")
async def start_study_mode(message: Message):
    """Початок вивчення в обраному режимі"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    module_id = state["module_id"]
    mode = message.text
    
    if mode == "🔙 До вибору набору":
        await choose_module_to_study(message)
        return
    
    if mode not in ["📝 Картки", "✅ Тест: Правильно/Неправильно", 
                    "🔢 Тест: 4 варіанти", "⌨️ Введення перекладу", 
                    "🧠 Режим заучування"]:
        await message.answer("❌ Оберіть режим зі списку!")
        return
    
    # Отримуємо слова для вивчення
    all_words = await WordsModel.get_module_words(module_id)
    learned_word_ids = await UserProgressModel.get_learned_words(user_id, module_id)
    
    # Фільтруємо невивчені слова
    words_to_study = [w for w in all_words if w["id"] not in learned_word_ids]
    
    if not words_to_study:
        # Якщо всі слова вивчені, питаємо чи скинути прогрес
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Скинути прогрес", callback_data=f"reset_progress:{module_id}")],
            [InlineKeyboardButton(text="📚 Вибрати інший набір", callback_data="choose_other_module")]
        ])
        
        await message.answer(
            "🎉 Вітаю! Ви вивчили всі слова в цьому наборі!\n"
            "Бажаєте скинути прогрес і почати заново?",
            reply_markup=keyboard
        )
        return
    
    user_states[user_id].update({
        "mode": mode,
        "step": "study_active",
        "words_to_study": words_to_study,
        "current_index": 0,
        "correct_answers": 0,
        "total_answers": 0
    })
    
    if mode == "🧠 Режим заучування":
        await start_learning_mode(message, user_id)
    else:
        await show_next_word(message, user_id)

async def start_learning_mode(message: Message, user_id: int):
    """Запуск режиму заучування"""
    state = user_states[user_id]
    module_id = state["module_id"]
    words_to_study = state["words_to_study"]
    
    # Розбиваємо на батчі
    batch_size = config.BATCH_SIZE
    batches = [words_to_study[i:i + batch_size] for i in range(0, len(words_to_study), batch_size)]
    
    # Перевіряємо збережений прогрес
    progress = await LearningProgressModel.get_progress(user_id, module_id)
    
    if progress:
        current_batch = progress["current_batch"]
        current_word_index = progress["current_word_index"]
        
        if current_batch < len(batches):
            state["current_batch"] = current_batch
            state["current_word_index"] = current_word_index
        else:
            state["current_batch"] = 0
            state["current_word_index"] = 0
    else:
        state["current_batch"] = 0
        state["current_word_index"] = 0
    
    current_batch_words = batches[state["current_batch"]]
    state["current_batch_words"] = current_batch_words
    state["batches"] = batches
    state["learn_phase"] = "view"
    state["viewed_cards"] = 0
    
    await message.answer(
        f"🧠 <b>Режим заучування</b>\n\n"
        f"📚 Група {state['current_batch'] + 1}/{len(batches)}\n"
        f"📝 Слів у групі: {len(current_batch_words)}\n\n"
        "Спочатку перегляньте всі картки:"
    )
    
    await show_learning_flashcard(message, user_id)

async def show_learning_flashcard(message: Message, user_id: int):
    """Показ картки в режимі заучування"""
    state = user_states[user_id]
    current_batch_words = state["current_batch_words"]
    
    if state["viewed_cards"] < len(current_batch_words):
        word_data = current_batch_words[state["viewed_cards"]]
        
        await message.answer(
            f"📝 Слово: <b>{word_data['word']}</b>",
            reply_markup=get_flashcard_keyboard()
        )
        
        state["current_word"] = word_data
        state["step"] = "showing_flashcard"
    else:
        # Переходимо до тестування
        state["learn_phase"] = "choice_test"
        state["tested_cards"] = 0
        await message.answer(
            "📝 Тепер перевіримо ваші знання!\n"
            "Оберіть правильний переклад:"
        )
        await start_learning_test(message, user_id)

@router.message(F.text == "👁️ Показати переклад")
async def show_translation_learning(message: Message):
    """Показ перекладу в режимі заучування"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if state.get("step") == "showing_flashcard" and "current_word" in state:
        word_data = state["current_word"]
        await message.answer(
            f"📝 Слово: <b>{word_data['word']}</b>\n"
            f"🔄 Переклад: <b>{word_data['translation']}</b>",
            reply_markup=get_know_dont_know_keyboard()
        )
        state["step"] = "showing_translation"
    else:
        await message.answer("❌ Спочатку оберіть режим заучування")

@router.message(F.text == "✅ Знаю")
@router.message(F.text == "❌ Не знаю")
async def handle_know_dont_know(message: Message):
    """Обробка відповіді Знаю/Не знаю"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if state.get("step") != "showing_translation":
        return
    
    is_known = message.text == "✅ Знаю"
    word_data = state["current_word"]
    
    # Оновлюємо статус слова
    if is_known:
        await UserProgressModel.update_word_status(
            user_id, state["module_id"], word_data["id"], "learned"
        )
    
    state["viewed_cards"] += 1
    await show_learning_flashcard(message, user_id)

async def start_learning_test(message: Message, user_id: int):
    """Початок тестування в режимі заучування"""
    state = user_states[user_id]
    current_batch_words = state["current_batch_words"]
    
    if state["tested_cards"] < len(current_batch_words):
        word_data = current_batch_words[state["tested_cards"]]
        
        # Генеруємо варіанти відповідей
        other_words = [w for w in current_batch_words if w["id"] != word_data["id"]]
        options = [word_data["translation"]]
        
        # Додаємо випадкові переклади
        for other in other_words[:3]:
            if other["translation"] not in options:
                options.append(other["translation"])
        
        # Якщо недостатньо варіантів, беремо з інших слів модуля
        if len(options) < 4:
            all_words = await WordsModel.get_module_words(state["module_id"])
            other_translations = [
                w["translation"] for w in all_words 
                if w["translation"] != word_data["translation"] 
                and w["translation"] not in options
            ]
            options.extend(other_translations[:4 - len(options)])
        
        options = options[:4]
        random.shuffle(options)
        
        state["current_word"] = word_data
        state["correct_answer"] = word_data["translation"]
        state["step"] = "learning_test"
        
        await message.answer(
            f"📝 <b>{word_data['word']}</b>\n\nОберіть правильний переклад:",
            reply_markup=get_choice_test_keyboard(options)
        )
    else:
        # Переходимо до письмового тесту
        state["learn_phase"] = "writing_test"
        state["written_cards"] = 0
        await message.answer(
            "⌨️ Тепер напишіть переклад кожного слова:"
        )
        await start_writing_test(message, user_id)

async def start_writing_test(message: Message, user_id: int):
    """Початок письмового тесту"""
    state = user_states[user_id]
    current_batch_words = state["current_batch_words"]
    
    if state["written_cards"] < len(current_batch_words):
        word_data = current_batch_words[state["written_cards"]]
        
        state["current_word"] = word_data
        state["correct_answer"] = word_data["translation"]
        state["step"] = "writing_test"
        
        await message.answer(
            f"📝 <b>{word_data['word']}</b>\n\nНапишіть переклад:",
            reply_markup=get_writing_test_keyboard()
        )
    else:
        # Завершуємо батч
        await finish_batch(message, user_id)

async def finish_batch(message: Message, user_id: int):
    """Завершення поточного батчу"""
    state = user_states[user_id]
    module_id = state["module_id"]
    
    # Відмічаємо всі слова батчу як вивчені
    for word_data in state["current_batch_words"]:
        await UserProgressModel.update_word_status(
            user_id, module_id, word_data["id"], "learned"
        )
    
    # Переходимо до наступного батчу
    state["current_batch"] += 1
    
    if state["current_batch"] < len(state["batches"]):
        # Зберігаємо прогрес
        await LearningProgressModel.save_progress(
            user_id, module_id, state["current_batch"], 0
        )
        
        state["current_batch_words"] = state["batches"][state["current_batch"]]
        state["learn_phase"] = "view"
        state["viewed_cards"] = 0
        
        await message.answer(
            f"✅ Групу {state['current_batch']}/{len(state['batches'])} завершено!\n"
            f"📚 Переходимо до наступної групи:"
        )
        await show_learning_flashcard(message, user_id)
    else:
        # Всі батчі завершені
        await message.answer(
            "🎉 Вітаю! Ви успішно вивчили всі слова в цьому наборі!\n"
            "Продовжуйте практикуватися для кращого запам'ятовування!",
            reply_markup=get_main_menu() if user_id != config.ADMIN_ID else get_admin_menu()
        )
        user_states[user_id] = {}

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "learning_test")
async def handle_learning_test_answer(message: Message):
    """Обробка відповіді в тесті"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text == "🔙 До меню":
        await back_to_menu(message)
        return
    
    correct_answer = state["correct_answer"]
    is_correct = message.text == correct_answer
    
    if is_correct:
        await message.answer("✅ Правильно! Молодець!")
    else:
        await message.answer(f"❌ Неправильно. Правильна відповідь: <b>{correct_answer}</b>")
    
    state["tested_cards"] += 1
    await start_learning_test(message, user_id)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "writing_test")
async def handle_writing_test_answer(message: Message):
    """Обробка відповіді в письмовому тесті"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text == "🔙 До меню":
        await back_to_menu(message)
        return
    
    if message.text == "❌ Не знаю":
        await message.answer(
            f"Правильний переклад: <b>{state['correct_answer']}</b>"
        )
    else:
        user_answer = message.text.strip().lower()
        correct_answer = state["correct_answer"].lower()
        
        if user_answer == correct_answer:
            await message.answer("✅ Правильно!")
        else:
            await message.answer(
                f"❌ Неправильно. Правильна відповідь: <b>{state['correct_answer']}</b>"
            )
    
    state["written_cards"] += 1
    await start_writing_test(message, user_id)

async def show_next_word(message: Message, user_id: int):
    """Показ наступного слова в звичайних режимах"""
    state = user_states[user_id]
    words_to_study = state["words_to_study"]
    current_index = state["current_index"]
    mode = state["mode"]
    
    if current_index >= len(words_to_study):
        # Завершення вивчення
        correct = state.get("correct_answers", 0)
        total = state.get("total_answers", 0)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        await message.answer(
            f"🎉 Ви завершили вивчення набору!\n\n"
            f"📊 Результати:\n"
            f"✅ Правильних відповідей: {correct}/{total}\n"
            f"📈 Точність: {accuracy:.1f}%",
            reply_markup=get_main_menu() if user_id != config.ADMIN_ID else get_admin_menu()
        )
        user_states[user_id] = {}
        return
    
    word_data = words_to_study[current_index]
    state["current_word"] = word_data
    
    if mode == "📝 Картки":
        await message.answer(
            f"📝 Слово: <b>{word_data['word']}</b>",
            reply_markup=get_flashcard_keyboard()
        )
        state["step"] = "flashcard_mode"
        
    elif mode == "✅ Тест: Правильно/Неправильно":
        # Випадково показуємо правильний або неправильний переклад
        if random.random() < 0.5:
            displayed_translation = word_data["translation"]
            is_correct = True
        else:
            other_words = [w for w in words_to_study if w["id"] != word_data["id"]]
            if other_words:
                displayed_translation = random.choice(other_words)["translation"]
            else:
                displayed_translation = word_data["translation"]
            is_correct = displayed_translation == word_data["translation"]
        
        state["displayed_translation"] = displayed_translation
        state["is_correct_displayed"] = is_correct
        
        await message.answer(
            f"📝 <b>{word_data['word']}</b>\n\n"
            f"Переклад: {displayed_translation}\n\n"
            "Це правильний переклад?",
            reply_markup=get_know_dont_know_keyboard()
        )
        state["step"] = "true_false_mode"
        
    elif mode == "🔢 Тест: 4 варіанти":
        # Генеруємо варіанти
        options = [word_data["translation"]]
        other_words = [w for w in words_to_study if w["id"] != word_data["id"]]
        
        for other in other_words[:3]:
            if other["translation"] not in options:
                options.append(other["translation"])
        
        if len(options) < 4:
            all_words = await WordsModel.get_module_words(state["module_id"])
            other_translations = [
                w["translation"] for w in all_words 
                if w["translation"] != word_data["translation"] 
                and w["translation"] not in options
            ]
            options.extend(other_translations[:4 - len(options)])
        
        options = options[:4]
        random.shuffle(options)
        
        state["correct_answer"] = word_data["translation"]
        
        await message.answer(
            f"📝 <b>{word_data['word']}</b>\n\nОберіть правильний переклад:",
            reply_markup=get_choice_test_keyboard(options)
        )
        state["step"] = "choice_mode"
        
    elif mode == "⌨️ Введення перекладу":
        await message.answer(
            f"📝 <b>{word_data['word']}</b>\n\nНапишіть переклад:",
            reply_markup=get_writing_test_keyboard()
        )
        state["step"] = "writing_mode"

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "flashcard_mode")
async def handle_flashcard_mode(message: Message):
    """Обробка режиму карток"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text == "👁️ Показати переклад":
        word_data = state["current_word"]
        await message.answer(
            f"📝 Слово: <b>{word_data['word']}</b>\n"
            f"🔄 Переклад: <b>{word_data['translation']}</b>",
            reply_markup=get_know_dont_know_keyboard()
        )
        state["step"] = "flashcard_translation"
    elif message.text == "🔙 До меню":
        await back_to_menu(message)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "flashcard_translation")
async def handle_flashcard_translation(message: Message):
    """Обробка відповіді після показу перекладу"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text in ["✅ Знаю", "❌ Не знаю"]:
        is_known = message.text == "✅ Знаю"
        word_data = state["current_word"]
        
        if is_known:
            await UserProgressModel.update_word_status(
                user_id, state["module_id"], word_data["id"], "learned"
            )
        
        state["current_index"] += 1
        state["total_answers"] = state.get("total_answers", 0) + 1
        if is_known:
            state["correct_answers"] = state.get("correct_answers", 0) + 1
        
        await show_next_word(message, user_id)
    elif message.text == "🔙 До меню":
        await back_to_menu(message)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "true_false_mode")
async def handle_true_false_mode(message: Message):
    """Обробка режиму Правильно/Неправильно"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text in ["✅ Правильно", "❌ Неправильно"]:
        user_says_correct = message.text == "✅ Правильно"
        actual_correct = state["is_correct_displayed"]
        is_correct = user_says_correct == actual_correct
        word_data = state["current_word"]
        
        if is_correct:
            await message.answer("✅ Правильно!")
            await UserProgressModel.update_word_status(
                user_id, state["module_id"], word_data["id"], "learned"
            )
        else:
            await message.answer(
                f"❌ Неправильно. Правильний переклад: <b>{word_data['translation']}</b>"
            )
        
        state["current_index"] += 1
        state["total_answers"] = state.get("total_answers", 0) + 1
        if is_correct:
            state["correct_answers"] = state.get("correct_answers", 0) + 1
        
        await show_next_word(message, user_id)
    elif message.text == "🔙 До меню":
        await back_to_menu(message)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "choice_mode")
async def handle_choice_mode(message: Message):
    """Обробка режиму з 4 варіантами"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text == "🔙 До меню":
        await back_to_menu(message)
        return
    
    is_correct = message.text == state["correct_answer"]
    word_data = state["current_word"]
    
    if is_correct:
        await message.answer("✅ Правильно! Молодець!")
        await UserProgressModel.update_word_status(
            user_id, state["module_id"], word_data["id"], "learned"
        )
    else:
        await message.answer(
            f"❌ Неправильно. Правильна відповідь: <b>{state['correct_answer']}</b>"
        )
    
    state["current_index"] += 1
    state["total_answers"] = state.get("total_answers", 0) + 1
    if is_correct:
        state["correct_answers"] = state.get("correct_answers", 0) + 1
    
    await show_next_word(message, user_id)

@router.message(lambda msg: msg.from_user.id in user_states and 
                user_states[msg.from_user.id].get("step") == "writing_mode")
async def handle_writing_mode(message: Message):
    """Обробка режиму введення перекладу"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if message.text == "🔙 До меню":
        await back_to_menu(message)
        return
    
    if message.text == "❌ Не знаю":
        await message.answer(
            f"Правильний переклад: <b>{state['current_word']['translation']}</b>"
        )
        is_correct = False
    else:
        user_answer = message.text.strip().lower()
        correct_answer = state["current_word"]["translation"].lower()
        is_correct = user_answer == correct_answer
        
        if is_correct:
            await message.answer("✅ Правильно!")
            await UserProgressModel.update_word_status(
                user_id, state["module_id"], state["current_word"]["id"], "learned"
            )
        else:
            await message.answer(
                f"❌ Неправильно. Правильна відповідь: <b>{state['current_word']['translation']}</b>"
            )
    
    state["current_index"] += 1
    state["total_answers"] = state.get("total_answers", 0) + 1
    if is_correct:
        state["correct_answers"] = state.get("correct_answers", 0) + 1
    
    await show_next_word(message, user_id)

@router.callback_query(F.data.startswith("reset_progress:"))
async def reset_module_progress(callback: CallbackQuery):
    """Скидання прогресу по модулю"""
    module_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    success = await UserProgressModel.reset_module_progress(user_id, module_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Прогрес успішно скинуто! Можете починати вивчення заново."
        )
    else:
        await callback.message.edit_text(
            "❌ Помилка скидання прогресу. Спробуйте пізніше."
        )
    
    await callback.answer()

@router.callback_query(F.data == "choose_other_module")
async def choose_other_module(callback: CallbackQuery):
    """Вибір іншого модуля"""
    await callback.message.delete()
    await choose_module_to_study(callback.message)
    await callback.answer()