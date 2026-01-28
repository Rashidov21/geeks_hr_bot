"""
HR application handlers - Job application flow
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, GROUP_ID
from db import save_application
from handlers.utils import validate_phone, validate_age, validate_name

logger = logging.getLogger(__name__)

router = Router()

# Constants
VACANCIES = ["Sotuvchi", "Admin", "Mentor", "Support"]
MENTOR_SUBJECTS = ["SMM", "Mobilografiya", "Dasturlash"]


# FSM States for HR
class HRForm(StatesGroup):
    choosing_vacancy = State()
    writing_name = State()
    writing_age = State()
    writing_phone = State()
    choosing_subject = State()
    writing_experience = State()
    writing_workplace = State()
    uploading_photo = State()
    uploading_cv = State()


# Helper function to send application to admin
async def send_application_to_admin(bot, data: dict) -> None:
    """Send application notification to admin and group."""
    text = (
        "📥 <b>Yangi ariza</b>\n\n"
        f"👤 Ism: {data.get('name')}\n"
        f"📅 Yosh: {data.get('age')}\n"
        f"📞 Tel: {data.get('phone')}\n"
        f"🏢 Vakansiya: {data.get('vacancy')}\n"
    )

    if data.get("vacancy") == "Mentor":
        text += f"📚 Yo'nalish: {data.get('subject')}\n"
        text += f"💼 Tajriba: {data.get('experience')}\n"
    else:
        text += f"💼 Tajriba: {data.get('experience')}\n"
        text += f"🏭 Ish joyi: {data.get('workplace')}\n"

    text += f"🔗 Username: @{data.get('username', 'N/A')}"

    for chat in (ADMIN_ID, GROUP_ID):
        try:
            await bot.send_message(chat_id=chat, text=text)
            if data.get("photo_id"):
                await bot.send_photo(chat_id=chat, photo=data["photo_id"])
            if data.get("cv_file_id"):
                await bot.send_document(chat_id=chat, document=data["cv_file_id"])
        except Exception as e:
            logger.exception(f"Error sending application to {chat}: {e}")


@router.message(Command("hr_start"))
async def cmd_hr_start(message: Message, state: FSMContext):
    """Handle HR application start - called from main menu."""
    await state.clear()
    chat_id = message.chat.id

    reply_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔄 Botni qayta ishga tushirish")]],
        resize_keyboard=True,
    )
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=vac, callback_data=f"hr_vac:{vac}")]
            for vac in VACANCIES
        ]
    )
    await message.answer(
        "👋 Assalomu alaykum!\n"
        "Men orqali Geeks Andijan o'quv markaziga ish uchun ariza topshirishingiz mumkin.\n\n"
        "Vakansiyani tanlang yoki pastdagi tugmani bosing:",
        reply_markup=reply_kb,
    )
    await message.answer("Vakansiyani tanlang:", reply_markup=inline_kb)

    await state.set_state(HRForm.choosing_vacancy)


@router.callback_query(F.data.startswith("hr_vac:"))
async def choose_vacancy(callback: CallbackQuery, state: FSMContext):
    """Handle vacancy selection."""
    vacancy = callback.data.split(":", 1)[1]
    if vacancy not in VACANCIES:
        await callback.answer("Noto'g'ri vakansiya", show_alert=True)
        return

    await state.update_data(vacancy=vacancy)
    await state.set_state(HRForm.writing_name)
    await callback.message.answer(
        f"🏢 Siz tanladingiz: {vacancy}\n\nEndi ism-familiyangizni kiriting:"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hr_sub:"))
async def choose_subject(callback: CallbackQuery, state: FSMContext):
    """Handle subject selection for Mentor."""
    subject = callback.data.split(":", 1)[1]
    if subject not in MENTOR_SUBJECTS:
        await callback.answer("Noto'g'ri yo'nalish", show_alert=True)
        return

    await state.update_data(subject=subject)
    await state.set_state(HRForm.writing_experience)
    await callback.message.answer("💼 Necha yillik tajribangiz bor?")
    await callback.answer()


@router.message(HRForm.writing_name)
async def process_name(message: Message, state: FSMContext):
    """Process name input."""
    if not validate_name(message.text):
        await message.answer("❗ Iltimos, to'g'ri ism-familiya kiriting (2-100 belgi).")
        return
    await state.update_data(
        name=message.text.strip(), username=message.from_user.username or "N/A"
    )
    await state.set_state(HRForm.writing_age)
    await message.answer("📅 Yoshni kiriting:")


@router.message(HRForm.writing_age)
async def process_age(message: Message, state: FSMContext):
    """Process age input."""
    ok, age = validate_age(message.text)
    if not ok:
        await message.answer("❗ Iltimos, to'g'ri yosh kiriting (16-100).")
        return
    await state.update_data(age=str(age))
    await state.set_state(HRForm.writing_phone)
    await message.answer("📞 Telefon raqamingizni yuboring:")


@router.message(HRForm.writing_phone)
async def process_phone(message: Message, state: FSMContext):
    """Process phone input."""
    if not validate_phone(message.text):
        await message.answer(
            "❗ Iltimos, to'g'ri telefon raqam kiriting.\n"
            "Misol: +998901234567 yoki 998901234567"
        )
        return
    data = await state.get_data()
    await state.update_data(phone=message.text.strip())

    if data.get("vacancy") == "Mentor":
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=sub, callback_data=f"hr_sub:{sub}")]
                for sub in MENTOR_SUBJECTS
            ]
        )
        await message.answer(
            "📚 Qaysi yo'nalishda dars bera olasiz?", reply_markup=inline_kb
        )
        await state.set_state(HRForm.choosing_subject)
    else:
        await state.set_state(HRForm.writing_experience)
        await message.answer("💼 Necha yillik tajribangiz bor?")


@router.message(HRForm.writing_experience)
async def process_experience(message: Message, state: FSMContext):
    """Process experience input."""
    await state.update_data(experience=message.text.strip())
    data = await state.get_data()
    if data.get("vacancy") == "Mentor":
        await state.set_state(HRForm.uploading_photo)
        await message.answer("🖼 Iltimos, o'z rasmingizni yuboring:")
    else:
        await state.set_state(HRForm.writing_workplace)
        await message.answer("🏭 Oldin qayerda ishlagansiz?")


@router.message(HRForm.writing_workplace)
async def process_workplace(message: Message, state: FSMContext):
    """Process workplace input."""
    await state.update_data(workplace=message.text.strip())
    await state.set_state(HRForm.uploading_photo)
    await message.answer("🖼 Iltimos, o'z rasmingizni yuboring:")


@router.message(HRForm.uploading_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Process photo upload."""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(HRForm.uploading_cv)
    await message.answer(
        "📄 Agar sizda CV (Rezyume) fayl bo'lsa, yuboring (PDF/DOCX).\n"
        "Aks holda 'Yo'q' deb yozing."
    )


@router.message(HRForm.uploading_photo)
async def process_photo_invalid(message: Message, state: FSMContext):
    """Handle invalid input when photo expected."""
    await message.answer("❗ Iltimos, faqat rasm yuboring.")


@router.message(HRForm.uploading_cv, F.document)
async def process_cv_document(message: Message, state: FSMContext):
    """Process CV document upload."""
    cv_id = message.document.file_id
    await state.update_data(cv_file_id=cv_id)
    await finish_application(message, state)


@router.message(HRForm.uploading_cv)
async def process_cv_text_or_invalid(message: Message, state: FSMContext):
    """Process CV skip or invalid input."""
    text = (message.text or "").strip().lower()
    if text in ["yo'q", "yoq", "yo'q", "yoq", "нет", "no"]:
        await state.update_data(cv_file_id=None)
        await finish_application(message, state)
    else:
        await message.answer("❗ Iltimos, CV yuboring yoki 'Yo'q' deb yozing.")


async def finish_application(message: Message, state: FSMContext):
    """Complete and save application."""
    data = await state.get_data()
    if not data.get("name") or not data.get("vacancy"):
        await message.answer(
            "❗ Ariza to'liq emas. Iltimos, /start bilan qaytadan boshlang."
        )
        await state.clear()
        return

    try:
        app_id = save_application(data)
        logger.info(f"Application saved with id {app_id}")
        await send_application_to_admin(message.bot, data)
        await message.answer(
            "✅ Rahmat! Arizangiz qabul qilindi. Tez orada siz bilan bog'lanamiz."
        )
    except Exception as e:
        logger.exception(f"Error saving application: {e}")
        await message.answer(
            "❗ Arizani saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )

    await state.clear()
