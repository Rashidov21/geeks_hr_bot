"""
Common handlers - Main menu, FAQ, contacts
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, is_admin
from handlers.hr import cmd_hr_start
from handlers.courses import COURSES

logger = logging.getLogger(__name__)

router = Router()

# FAQ keywords and responses (umumiy qisqa savollar)
FAQ_RESPONSES = {
    "narx": (
        "💰 <b>Narxlar</b>\n\n"
        "Kurslar narxlari:\n"
        "• SMM: Narx menejer orqali\n"
        "• Mobilografiya: Narx menejer orqali\n"
        "• Computer Science: Oyiga 800 000 so'm\n"
        "• Python Fullstack dasturlash: Oyiga 800 000 so'm\n\n"
        "Aniq narxlar va to'lov shartlari bo'yicha menejerimiz bilan bog'laning."
    ),
    "qancha turadi": (
        "💰 <b>Narxlar</b>\n\n"
        "Kurslar narxlari:\n"
        "• SMM: Narx menejer orqali\n"
        "• Mobilografiya: Narx menejer orqali\n"
        "• Computer Science: Oyiga 800 000 so'm\n"
        "• Python Fullstack dasturlash: Oyiga 800 000 so'm\n\n"
        "Aniq narxlar va to'lov shartlari bo'yicha menejerimiz bilan bog'laning."
    ),
    "manzil": (
        "📍 <b>Geeks Andijan filial manzillari</b>\n\n"
        "Geeks Andijan markaziy filial:\n"
        "📍 Andijon shahri, Bobur shox ko'chasi, 92-uy (Sakura binosi oldida)\n"
        "Xarita: https://yandex.uz/maps/-/CLxa5AiB\n\n"
        "Geeks Poytug':\n"
        "📍 Izboskan tumani, Chirmash Azimov ko'chasi, 39-uy\n"
        "Xarita: https://yandex.uz/maps/-/CLxgVL5U\n\n"
        "Geeks Jalaquduq:\n"
        "📍 Jalaquduq tumani, 3-maktab yonida\n\n"
        "⏰ Ish vaqti: 9:00 – 19:00 (Dushanba – Shanba)"
    ),
    "qayerda joylashgan": (
        "📍 <b>Geeks Andijan filial manzillari</b>\n\n"
        "Geeks Andijan markaziy filial:\n"
        "📍 Andijon shahri, Bobur shox ko'chasi, 92-uy (Sakura binosi oldida)\n"
        "Xarita: https://yandex.uz/maps/-/CLxa5AiB\n\n"
        "Geeks Poytug':\n"
        "📍 Izboskan tumani, Chirmash Azimov ko'chasi, 39-uy\n"
        "Xarita: https://yandex.uz/maps/-/CLxgVL5U\n\n"
        "Geeks Jalaquduq:\n"
        "📍 Jalaquduq tumani, 3-maktab yonida\n\n"
        "⏰ Ish vaqti: 9:00 – 19:00 (Dushanba – Shanba)"
    ),
    "aloqa": (
        "📞 <b>Kontaktlar</b>\n\n"
        "👨‍💼 Admin bilan bog'lanish:\n"
        "📱 Admin: @geeks_support\n\n"
        "☎️ Telefon raqamlari:\n"
        "📞 +998 90 211 31 23 (Yangi bozor, asosiy filial)\n"
        "📞 +998 90 173 21 11 (Poytug' filiali)\n\n"
        "📍 Manzil va batafsil ma'lumot uchun '📞 Kontaktlar / Manzil' tugmasini bosing."
    ),
    "telefon": (
        "📞 <b>Kontaktlar</b>\n\n"
        "👨‍💼 Admin bilan bog'lanish:\n"
        "📱 Admin: @geeks_support\n\n"
        "☎️ Telefon raqamlari:\n"
        "📞 +998 90 211 31 23 (Yangi bozor, asosiy filial)\n"
        "📞 +998 90 173 21 11 (Poytug' filiali)\n\n"
        "📍 Manzil va batafsil ma'lumot uchun '📞 Kontaktlar / Manzil' tugmasini bosing."
    ),
}

# Kurslarga oid FAQ larni ham umumiy FAQ bo'limiga qo'shamiz
# Kalit sifatida to'liq savol matni lower() ko'rinishida saqlanadi.
COURSE_FAQ_RESPONSES: dict[str, str] = {}

for course_name, data in COURSES.items():
    for q, a in data.get("faq", []):
        key = q.lower().strip()
        # Bir xil savol bir necha kursda bo'lsa, birinchisi qoladi
        if key not in COURSE_FAQ_RESPONSES:
            COURSE_FAQ_RESPONSES[key] = (
                f"📚 <b>{course_name}</b>\n\n"
                f"❔ {q}\n\n"
                f"{a}"
            )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - show main menu."""
    await state.clear()
    chat_id = message.chat.id

    if is_admin(chat_id):
        # Admin panel - alohida admin menu
        admin_reply_kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📋 Oxirgi arizalar"),
                    KeyboardButton(text="📤 Export"),
                ],
                [
                    KeyboardButton(text="📨 Support murojaatlar"),
                    KeyboardButton(text="📥 Export Support"),
                ],
                [
                    KeyboardButton(text="📝 Ishga ariza topshirish"),
                    KeyboardButton(text="🧑‍💻 Kurslar haqida ma'lumot"),
                ],
                [
                    KeyboardButton(text="❓ Savol berish (Support)"),
                    KeyboardButton(text="📞 Kontaktlar / Manzil"),
                ],
            ],
            resize_keyboard=True,
        )
        await message.answer(
            "👋 <b>Admin panel</b>\n\n"
            "Quyidagi tugmalardan foydalaning:",
            reply_markup=admin_reply_kb
        )
        return  # Admin uchun return qilamiz, umumiy menu ko'rsatilmaydi
    
    # Main menu for regular users
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Ishga ariza topshirish")],
            [KeyboardButton(text="🧑‍💻 Kurslar haqida ma'lumot")],
            [KeyboardButton(text="❓ Savol berish (Support)")],
            [KeyboardButton(text="📞 Kontaktlar / Manzil")],
        ],
        resize_keyboard=True,
    )
    
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Geeks Andijan o'quv markaziga xush kelibsiz!\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=reply_kb
    )


@router.message(F.text == "📝 Ishga ariza topshirish")
async def menu_hr(message: Message, state: FSMContext):
    """Handle HR application menu button."""
    await cmd_hr_start(message, state)


@router.message(F.text == "🧑‍💻 Kurslar haqida ma'lumot")
async def menu_courses(message: Message, state: FSMContext):
    """Handle courses menu button."""
    from handlers.courses import CoursesForm, COURSES
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await state.clear()
    await state.set_state(CoursesForm.choosing_course)
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course, callback_data=f"course:{course}")]
            for course in COURSES.keys()
        ]
    )
    
    await message.answer(
        "🧑‍💻 <b>Kurslar haqida ma'lumot</b>\n\n"
        "Qaysi kurs haqida ma'lumot olishni xohlaysiz?",
        reply_markup=inline_kb
    )


@router.message(F.text == "❓ Savol berish (Support)")
async def menu_support(message: Message, state: FSMContext):
    """Handle support menu button."""
    from handlers.support import SupportForm, SUPPORT_CATEGORIES
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await state.clear()
    await state.set_state(SupportForm.choosing_category)
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"sup_cat:{cat_key}")]
            for cat, cat_key in SUPPORT_CATEGORIES.items()
        ]
    )
    
    await message.answer(
        "❓ Savol berish\n\n"
        "Qaysi kategoriyaga tegishli savolingizni tanlang:",
        reply_markup=inline_kb
    )


@router.message(F.text == "📞 Kontaktlar / Manzil")
async def menu_contacts(message: Message):
    """Handle contacts menu button."""
    text = (
        "📞 <b>Kontaktlar va Manzil</b>\n\n"
        "👨‍💼 <b>Admin bilan bog'lanish:</b>\n"
        "📱 Admin: @geeks_support\n\n"
        "☎️ <b>Telefon raqamlari:</b>\n"
        "📞 +998 90 211 31 23 (Yangi bozor, asosiy filial)\n"
        "📞 +998 90 173 21 11 (Poytug' filiali)\n\n"
        "🏢 <b>Filial manzillari:</b>\n"
        "Geeks Andijan markaziy filial:\n"
        "📍 Andijon shahri, Bobur shox ko'chasi, 92-uy (Sakura binosi oldida)\n"
        "Xarita: https://yandex.uz/maps/-/CLxa5AiB\n\n"
        "Geeks Poytug':\n"
        "📍 Izboskan tumani, Chirmash Azimov ko'chasi, 39-uy\n"
        "Xarita: https://yandex.uz/maps/-/CLxgVL5U\n\n"
        "Geeks Jalaquduq:\n"
        "📍 Jalaquduq tumani, 3-maktab yonida\n\n"
        "⏰ <b>Ish vaqti:</b> 9:00 – 19:00 (Dushanba – Shanba)\n\n"
        "❓ Har qanday savol, taklif va yordam uchun bemalol yozing!"
    )
    await message.answer(text, disable_web_page_preview=True)


@router.message(F.text == "🔄 Botni qayta ishga tushirish")
async def restart_bot(message: Message, state: FSMContext):
    """Handle restart button."""
    await cmd_start(message, state)


@router.message()
async def faq_handler(message: Message, state: FSMContext):
    """
    FAQ handler - responds to common keywords when user is not in any FSM state.
    This should be the last handler in the router chain.
    """
    # Check if user is in any FSM state
    current_state = await state.get_state()
    if current_state is not None:
        # User is in a flow, don't interfere
        return
    
    # Check for FAQ keywords
    text = (message.text or "").strip().lower()
    
    # 1) Umumiy qisqa FAQ javoblari
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in text:
            await message.answer(response, disable_web_page_preview=True)
            return

    # 2) Kurslarga oid FAQ lar (foydalanuvchi savolni to'liq yoki
    #    asosiy qismi bilan yozgan bo'lsa, mos javob qaytaramiz)
    for question_text, response in COURSE_FAQ_RESPONSES.items():
        if question_text in text:
            await message.answer(response, disable_web_page_preview=True)
            return
    
    # If no FAQ match, show main menu hint
    await message.answer(
        "❓ Nima yordam bera olaman?\n\n"
        "Quyidagilardan birini tanlang:\n"
        "• 📝 Ishga ariza topshirish\n"
        "• 🧑‍💻 Kurslar haqida ma'lumot\n"
        "• ❓ Savol berish (Support)\n"
        "• 📞 Kontaktlar / Manzil"
    )
