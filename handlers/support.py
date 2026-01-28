"""
Support handlers - Question/Support ticket flow
"""
import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import SUPPORT_GROUP_ID
from db import save_support_ticket
from handlers.utils import validate_phone

logger = logging.getLogger(__name__)

router = Router()

# Support categories
SUPPORT_CATEGORIES = {
    "📚 Kurslar": "courses",
    "💳 To'lov": "payment",
    "📍 Manzil": "location",
    "🔄 Boshqa": "other",
}


# FSM States for Support
class SupportForm(StatesGroup):
    choosing_category = State()
    writing_question = State()
    asking_phone = State()


def is_working_hours() -> bool:
    """
    Check if current time is within working hours (09:00-19:00).
    Uses timezone from config.
    """
    from datetime import timezone, timedelta
    from config import TIMEZONE_OFFSET
    # Timezone from config (default UTC+5)
    tz = timezone(timedelta(hours=TIMEZONE_OFFSET))
    current_time = datetime.now(tz)
    current_hour = current_time.hour
    # Working hours: 9:00 - 19:00 (Dushanba - Shanba)
    return 9 <= current_hour < 19


def escape_html(text: str | None) -> str:
    """Escape HTML special characters to prevent injection."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


async def send_ticket_to_support_group(
    bot, ticket_id: int, user_id: int, username: str, category: str, question: str, 
    voice_id: str | None = None, phone: str | None = None
):
    """Send support ticket to support group."""
    is_night = not is_working_hours()
    night_label = "[Night queue] " if is_night else ""
    
    # Escape HTML to prevent injection
    safe_username = escape_html(username)
    safe_phone = escape_html(phone)
    safe_category = escape_html(category)
    safe_question = escape_html(question)
    
    text = (
        f"{night_label}🎫 <b>Support Ticket #{ticket_id}</b>\n\n"
        f"👤 User: @{safe_username or 'N/A'} (ID: {user_id})\n"
        f"📂 Kategoriya: {safe_category}\n"
    )
    
    if phone:
        text += f"📞 Telefon: {safe_phone}\n"
    else:
        text += "📞 Telefon: ko'rsatilmagan\n"
    
    text += f"\n❓ Savol:\n{safe_question}"
    
    if voice_id:
        text += f"\n\n🎤 Ovozli xabar mavjud (file_id: {voice_id})"
    
    try:
        await bot.send_message(chat_id=SUPPORT_GROUP_ID, text=text)
        if voice_id:
            await bot.send_voice(chat_id=SUPPORT_GROUP_ID, voice=voice_id)
    except Exception as e:
        logger.exception(f"Error sending ticket to support group: {e}")


@router.callback_query(F.data == "menu_support")
async def start_support(callback: CallbackQuery, state: FSMContext):
    """Start support flow from main menu."""
    await state.clear()
    await state.set_state(SupportForm.choosing_category)
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"sup_cat:{cat_key}")]
            for cat, cat_key in SUPPORT_CATEGORIES.items()
        ]
    )
    
    await callback.message.answer(
        "❓ Savol berish\n\n"
        "Qaysi kategoriyaga tegishli savolingizni tanlang:",
        reply_markup=inline_kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sup_cat:"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection."""
    category_key = callback.data.split(":", 1)[1]
    if category_key not in SUPPORT_CATEGORIES.values():
        await callback.answer("Noto'g'ri kategoriya", show_alert=True)
        return
    
    category_name = [k for k, v in SUPPORT_CATEGORIES.items() if v == category_key][0]
    await state.update_data(category=category_name, category_key=category_key)
    await state.set_state(SupportForm.writing_question)
    
    await callback.message.answer(
        f"📂 Kategoriya: {category_name}\n\n"
        "Savolingizni yozing yoki ovozli xabar sifatida yuboring:"
    )
    await callback.answer()


@router.message(SupportForm.writing_question, F.text)
async def process_question_text(message: Message, state: FSMContext):
    """Process text question."""
    question = message.text.strip()
    if len(question) < 5:
        await message.answer("❗ Iltimos, savolingizni batafsilroq yozing (kamida 5 belgi).")
        return
    
    await state.update_data(question=question, question_voice_id=None)
    
    # Check if phone number is mentioned in question (improved pattern)
    # Extract potential phone numbers from text - matches various formats
    # Matches: +998901234567, 998901234567, 901234567, +998 90 123 45 67, etc.
    phone_pattern = r'\+?998\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2}|\+?998\d{9}|998\d{9}|\d{9,12}'
    # Remove spaces and dashes for matching
    cleaned_question = question.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    phone_matches = re.findall(phone_pattern, cleaned_question)
    phone_in_text = False
    if phone_matches:
        # Try to validate the first match
        for match in phone_matches:
            # Clean the match
            cleaned_match = re.sub(r'[\s\-\(\)]', '', match)
            if validate_phone(cleaned_match):
                phone_in_text = True
                await state.update_data(phone=cleaned_match)
                break
    
    if not phone_in_text:
        await state.set_state(SupportForm.asking_phone)
        await message.answer(
            "📞 Agar tezroq bog'lanishimizni istasangiz, telefon raqamingizni ham yozib qoldiring:\n"
            "(Yoki 'O'tkazib yuborish' tugmasini bosing)"
        )
    else:
        await finish_support_ticket(message, state)


@router.message(SupportForm.writing_question, F.voice)
async def process_question_voice(message: Message, state: FSMContext):
    """Process voice question."""
    voice_id = message.voice.file_id
    await state.update_data(question="Ovozli xabar", question_voice_id=voice_id)
    await state.set_state(SupportForm.asking_phone)
    
    await message.answer(
        "🎤 Ovozli xabaringiz qabul qilindi.\n\n"
        "📞 Agar tezroq bog'lanishimizni istasangiz, telefon raqamingizni ham yozib qoldiring:\n"
        "(Yoki 'O'tkazib yuborish' tugmasini bosing)"
    )


@router.message(SupportForm.writing_question)
async def process_question_invalid(message: Message, state: FSMContext):
    """Handle invalid input when question expected."""
    await message.answer("❗ Iltimos, savolingizni matn yoki ovozli xabar sifatida yuboring.")


@router.message(SupportForm.asking_phone, F.text)
async def process_support_phone(message: Message, state: FSMContext):
    """Process phone number for support."""
    text = message.text.strip().lower()
    
    if text in ["o'tkazib yuborish", "otkazib yuborish", "skip", "o'tkaz"]:
        await finish_support_ticket(message, state)
        return
    
    if validate_phone(message.text):
        await state.update_data(phone=message.text.strip())
        await finish_support_ticket(message, state)
    else:
        await message.answer(
            "❗ Iltimos, to'g'ri telefon raqam kiriting yoki 'O'tkazib yuborish' deb yozing.\n"
            "Misol: +998901234567"
        )


async def finish_support_ticket(message: Message, state: FSMContext):
    """Complete and save support ticket."""
    data = await state.get_data()
    if not data.get("category") or not data.get("question"):
        await message.answer(
            "❗ Savol to'liq emas. Iltimos, /start bilan qaytadan boshlang."
        )
        await state.clear()
        return
    
    try:
        ticket_id = save_support_ticket({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "phone": data.get("phone"),
            "category": data.get("category"),
            "question": data.get("question"),
            "question_voice_id": data.get("question_voice_id"),
            "status": "pending",
        })
        
        logger.info(f"Support ticket saved with id {ticket_id}")
        
        # Send to support group
        await send_ticket_to_support_group(
            bot=message.bot,
            ticket_id=ticket_id,
            user_id=message.from_user.id,
            username=message.from_user.username,
            category=data.get("category"),
            question=data.get("question"),
            voice_id=data.get("question_voice_id"),
            phone=data.get("phone"),
        )
        
        # User response
        is_night = not is_working_hours()
        if is_night:
            await message.answer(
                "✅ Savolingiz qabul qilindi.\n\n"
                "⚠️ Savolingiz ish vaqtidan tashqarida qabul qilindi. "
                "Operatorlar ertasi kuni javob berishadi."
            )
        else:
            await message.answer(
                "✅ Savolingiz qabul qilindi. Operatorlar tez orada siz bilan bog'lanishadi."
            )
        
        # If phone was provided, mention it
        if data.get("phone"):
            await message.answer(
                f"📞 Telefon raqamingiz qayd etildi: {data.get('phone')}\n"
                "Menejerimiz sizga qo'ng'iroq qilishi mumkin."
            )
        
    except Exception as e:
        logger.exception(f"Error saving support ticket: {e}")
        await message.answer(
            "❗ Savolni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )
    
    await state.clear()
