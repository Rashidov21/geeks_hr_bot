"""
Aiogram-based HR Bot with SQLite and webhook support.
Run this file with: python bot_aiogram.py
"""

import asyncio
import logging
import re
import os
from typing import Dict, Any

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import (
    TOKEN,
    ADMIN_ID,
    GROUP_ID,
    SESSION_TIMEOUT,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBAPP_HOST,
    WEBAPP_PORT,
    WEBHOOK_SECRET,
)
from db import ensure_db, save_application, get_last_applicants, get_all_applicants

import openpyxl

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hr_bot_aiogram")


# ==========================
#   CONSTANTS
# ==========================

VACANCIES = ["Sotuvchi", "Admin", "Mentor", "Support"]
MENTOR_SUBJECTS = ["SMM", "Mobilografiya", "Dasturlash"]


# ==========================
#   FSM STATES
# ==========================


class Form(StatesGroup):
    choosing_vacancy = State()
    writing_name = State()
    writing_age = State()
    writing_phone = State()
    choosing_subject = State()
    writing_experience = State()
    writing_workplace = State()
    uploading_photo = State()
    uploading_cv = State()


# ==========================
#   VALIDATION
# ==========================


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    pattern = r"^\+?[1-9]\d{6,14}$"
    return bool(re.match(pattern, cleaned))


def validate_age(age_str: str) -> tuple[bool, int | None]:
    """Validate age input. Returns (is_valid, age_value)."""
    try:
        age = int(age_str.strip())
        if 16 <= age <= 100:
            return True, age
        return False, None
    except ValueError:
        return False, None


def validate_name(name: str) -> bool:
    """Validate name input (non-empty, reasonable length)."""
    name = name.strip()
    # Allow letters, spaces, apostrophes, and hyphens
    return 2 <= len(name) <= 100 and bool(re.match(r"^[\w\s'\-]+$", name, re.UNICODE))


# ==========================
#   BOT & DISPATCHER
# ==========================

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()


# ==========================
#   HELPERS
# ==========================


async def send_application_to_admin(data: Dict[str, Any]) -> None:
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


async def export_to_excel_file(vacancy: str | None = None) -> str | None:
    """Export applicants to Excel file. Returns file path or None."""
    rows = get_all_applicants(vacancy)
    if not rows:
        return None

    file_name = f"{vacancy}_arizalar.xlsx" if vacancy else "all_arizalar.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Arizalar"

    headers = [
        "ID",
        "Ism",
        "Yosh",
        "Telefon",
        "Vakansiya",
        "Yo'nalish",
        "Tajriba",
        "Ish joyi",
        "Username",
        "Rasm",
        "CV",
        "Sana",
    ]
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(file_name)
    return file_name


# ==========================
#   HANDLERS
# ==========================


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    await state.clear()
    chat_id = message.chat.id

    if chat_id == ADMIN_ID:
        # Admin panel
        reply_kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📋 Oxirgi arizalar"),
                    KeyboardButton(text="📤 Export"),
                ]
            ],
            resize_keyboard=True,
        )
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=vac, callback_data=f"vac:{vac}"
                    )
                ]
                for vac in VACANCIES
            ]
        )
        await message.answer(
            "👋 Admin panel.\nVakansiyani tanlang yoki pastdagi tugmalardan foydalaning:",
            reply_markup=reply_kb,
        )
        await message.answer("Vakansiyani tanlang:", reply_markup=inline_kb)
    else:
        reply_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔄 Botni qayta ishga tushirish")]],
            resize_keyboard=True,
        )
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=vac, callback_data=f"vac:{vac}"
                    )
                ]
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

    await state.set_state(Form.choosing_vacancy)


@dp.message(F.text == "🔄 Botni qayta ishga tushirish")
async def restart_bot(message: Message, state: FSMContext):
    """Handle restart button."""
    await cmd_start(message, state)


@dp.callback_query(F.data.startswith("vac:"))
async def choose_vacancy(callback: CallbackQuery, state: FSMContext):
    """Handle vacancy selection."""
    vacancy = callback.data.split(":", 1)[1]
    if vacancy not in VACANCIES:
        await callback.answer("Noto'g'ri vakansiya", show_alert=True)
        return

    await state.update_data(vacancy=vacancy)
    await state.set_state(Form.writing_name)
    await callback.message.answer(
        f"🏢 Siz tanladingiz: {vacancy}\n\nEndi ism-familiyangizni kiriting:"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("sub:"))
async def choose_subject(callback: CallbackQuery, state: FSMContext):
    """Handle subject selection for Mentor."""
    subject = callback.data.split(":", 1)[1]
    if subject not in MENTOR_SUBJECTS:
        await callback.answer("Noto'g'ri yo'nalish", show_alert=True)
        return

    await state.update_data(subject=subject)
    await state.set_state(Form.writing_experience)
    await callback.message.answer("💼 Necha yillik tajribangiz bor?")
    await callback.answer()


@dp.message(Form.writing_name)
async def process_name(message: Message, state: FSMContext):
    """Process name input."""
    if not validate_name(message.text):
        await message.answer("❗ Iltimos, to'g'ri ism-familiya kiriting (2-100 belgi).")
        return
    await state.update_data(
        name=message.text.strip(), username=message.from_user.username or "N/A"
    )
    await state.set_state(Form.writing_age)
    await message.answer("📅 Yoshni kiriting:")


@dp.message(Form.writing_age)
async def process_age(message: Message, state: FSMContext):
    """Process age input."""
    ok, age = validate_age(message.text)
    if not ok:
        await message.answer("❗ Iltimos, to'g'ri yosh kiriting (16-100).")
        return
    await state.update_data(age=str(age))
    await state.set_state(Form.writing_phone)
    await message.answer("📞 Telefon raqamingizni yuboring:")


@dp.message(Form.writing_phone)
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
                [InlineKeyboardButton(text=sub, callback_data=f"sub:{sub}")]
                for sub in MENTOR_SUBJECTS
            ]
        )
        await message.answer(
            "📚 Qaysi yo'nalishda dars bera olasiz?", reply_markup=inline_kb
        )
        await state.set_state(Form.choosing_subject)
    else:
        await state.set_state(Form.writing_experience)
        await message.answer("💼 Necha yillik tajribangiz bor?")


@dp.message(Form.writing_experience)
async def process_experience(message: Message, state: FSMContext):
    """Process experience input."""
    await state.update_data(experience=message.text.strip())
    data = await state.get_data()
    if data.get("vacancy") == "Mentor":
        await state.set_state(Form.uploading_photo)
        await message.answer("🖼 Iltimos, o'z rasmingizni yuboring:")
    else:
        await state.set_state(Form.writing_workplace)
        await message.answer("🏭 Oldin qayerda ishlagansiz?")


@dp.message(Form.writing_workplace)
async def process_workplace(message: Message, state: FSMContext):
    """Process workplace input."""
    await state.update_data(workplace=message.text.strip())
    await state.set_state(Form.uploading_photo)
    await message.answer("🖼 Iltimos, o'z rasmingizni yuboring:")


@dp.message(Form.uploading_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Process photo upload."""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(Form.uploading_cv)
    await message.answer(
        "📄 Agar sizda CV (Rezyume) fayl bo'lsa, yuboring (PDF/DOCX).\n"
        "Aks holda 'Yo'q' deb yozing."
    )


@dp.message(Form.uploading_photo)
async def process_photo_invalid(message: Message, state: FSMContext):
    """Handle invalid input when photo expected."""
    await message.answer("❗ Iltimos, faqat rasm yuboring.")


@dp.message(Form.uploading_cv, F.document)
async def process_cv_document(message: Message, state: FSMContext):
    """Process CV document upload."""
    cv_id = message.document.file_id
    await state.update_data(cv_file_id=cv_id)
    await finish_application(message, state)


@dp.message(Form.uploading_cv)
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
        await send_application_to_admin(data)
        await message.answer(
            "✅ Rahmat! Arizangiz qabul qilindi. Tez orada siz bilan bog'lanamiz."
        )
    except Exception as e:
        logger.exception(f"Error saving application: {e}")
        await message.answer(
            "❗ Arizani saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )

    await state.clear()


# ==========================
#   ADMIN HANDLERS
# ==========================


@dp.message(Command("last"))
async def cmd_last(message: Message, command: CommandObject):
    """Handle /last command for admin."""
    if message.chat.id != ADMIN_ID:
        return
    vacancy = None
    if command.args:
        vacancy = command.args.strip().capitalize()
    rows = get_last_applicants(limit=5, vacancy=vacancy)
    if not rows:
        await message.answer(f"{vacancy or 'Umumiy'} bo'yicha ariza topilmadi.")
        return
    text = "📋 Oxirgi arizalar"
    if vacancy:
        text += f" ({vacancy})"
    text += ":\n\n"
    for r in rows:
        text += (
            f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
        )
    await message.answer(text)


@dp.message(Command("export"))
async def cmd_export(message: Message, command: CommandObject):
    """Handle /export command for admin."""
    if message.chat.id != ADMIN_ID:
        return
    vacancy = None
    if command.args:
        vacancy = command.args.strip().capitalize()
    file_name = await export_to_excel_file(vacancy)
    if not file_name:
        await message.answer(f"{vacancy or 'Umumiy'} bo'yicha ariza topilmadi.")
        return
    try:
        file = FSInputFile(file_name)
        await message.answer_document(file)
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


@dp.message(F.text == "📋 Oxirgi arizalar")
async def last_button(message: Message):
    """Handle 'Last applications' button for admin."""
    if message.chat.id != ADMIN_ID:
        return
    rows = get_last_applicants(limit=5)
    if not rows:
        await message.answer("Arizalar topilmadi.")
        return
    text = "📋 Oxirgi arizalar:\n\n"
    for r in rows:
        text += (
            f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
        )
    await message.answer(text)


@dp.message(F.text == "📤 Export")
async def export_button(message: Message):
    """Handle 'Export' button for admin."""
    if message.chat.id != ADMIN_ID:
        return
    file_name = await export_to_excel_file()
    if not file_name:
        await message.answer("Arizalar topilmadi.")
        return
    try:
        file = FSInputFile(file_name)
        await message.answer_document(file)
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


# ==========================
#   WEBHOOK SERVER (aiohttp)
# ==========================


async def on_startup(app: web.Application):
    """Initialize database and set webhook on startup."""
    ensure_db()
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message", "callback_query", "edited_message", "channel_post"],
    )
    logger.info(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    """Cleanup on shutdown."""
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app() -> web.Application:
    """Create aiohttp application with webhook handler."""
    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Optional health endpoint
    async def health(request: web.Request):
        return web.json_response({"status": "ok"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    return app


async def main():
    """Main entry point."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    logger.info(f"Starting webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}")
    await site.start()

    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
