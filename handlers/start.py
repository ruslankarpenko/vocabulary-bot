from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from keyboards.main import get_main_menu, get_admin_menu
from config import config

router = Router()

# Імпортуємо user_states з main при потребі
from main import user_states

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обробник команди /start"""
    user_id = message.from_user.id
    
    # Ініціалізація стану користувача
    user_states[user_id] = {}
    
    welcome_text = (
        f"👋 Привіт, {message.from_user.full_name}!\n\n"
        "📚 Я бот для вивчення іноземних слів. З моєю допомогою ти зможеш:\n"
        "• Створювати власні набори слів\n"
        "• Вивчати слова в різних режимах\n"
        "• Ділитися наборами з іншими\n"
        "• Використовувати публічну бібліотеку\n\n"
        "Обери дію в меню нижче 👇"
    )
    
    # Перевірка чи це адміністратор
    if user_id == config.ADMIN_ID:
        await message.answer(
            welcome_text + "\n\n🔐 У вас є права адміністратора!",
            reply_markup=get_admin_menu()
        )
    else:
        await message.answer(welcome_text, reply_markup=get_main_menu())

@router.message(F.text == "🔙 До меню")
@router.message(F.text == "🔙 Головне меню")
async def back_to_menu(message: Message):
    """Повернення до головного меню"""
    user_id = message.from_user.id
    
    # Зберігаємо прогрес якщо є
    state = user_states.get(user_id, {})
    if "module_id" in state and "current_batch" in state:
        from database.models import LearningProgressModel
        await LearningProgressModel.save_progress(
            user_id,
            state["module_id"],
            state.get("current_batch", 0),
            state.get("current_word_index", 0)
        )
    
    # Очищаємо стан
    user_states[user_id] = {}
    
    if user_id == config.ADMIN_ID:
        await message.answer("Головне меню:", reply_markup=get_admin_menu())
    else:
        await message.answer("Головне меню:", reply_markup=get_main_menu())

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Допомога по використанню бота"""
    help_text = (
        "📖 <b>Допомога по використанню бота</b>\n\n"
        "<b>Створення набору:</b>\n"
        "1. Натисніть '📘 Створити набір'\n"
        "2. Введіть назву та опис\n"
        "3. Оберіть мови та категорію\n"
        "4. Вкажіть видимість (приватний/публічний)\n"
        "5. Додайте слова та переклади\n\n"
        "<b>Режими вивчення:</b>\n"
        "• 📝 Картки - перегляд слів\n"
        "• ✅ Тест: Правильно/Неправильно\n"
        "• 🔢 Тест: 4 варіанти\n"
        "• ⌨️ Введення перекладу\n"
        "• 🧠 Режим заучування - ефективне запам'ятовування\n\n"
        "<b>Публічна бібліотека:</b>\n"
        "• Переглядайте набори інших користувачів\n"
        "• Фільтруйте за мовами та категоріями\n"
        "• Додавайте набори до своєї бібліотеки\n\n"
        "Якщо виникли питання - звертайтесь до адміністратора"
    )
    await message.answer(help_text)