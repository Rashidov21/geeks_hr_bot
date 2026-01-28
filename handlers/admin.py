"""
Admin handlers - HR management and support reply
"""
import logging
import os
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile

from config import ADMIN_ID, SUPPORT_GROUP_ID
from db import get_last_applicants, get_all_applicants, get_support_tickets
import openpyxl

logger = logging.getLogger(__name__)

router = Router()


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


@router.message(Command("last"))
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


@router.message(Command("export"))
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


@router.message(F.text == "📋 Oxirgi arizalar")
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


@router.message(F.text == "📤 Export")
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


@router.message(Command("answer"))
async def cmd_answer(message: Message, command: CommandObject):
    """
    Handle /answer command for support group admins.
    Usage: /answer <user_id> <reply_text>
    """
    # Only allow from admin or support group
    if message.chat.id not in (ADMIN_ID, SUPPORT_GROUP_ID):
        return

    if not command.args:
        await message.answer(
            "❌ Format: /answer <user_id> <javob matni>\n"
            "Misol: /answer 123456789 Salom! Sizning savolingizga javob..."
        )
        return

    parts = command.args.split(None, 1)
    if len(parts) < 2:
        await message.answer(
            "❌ Format: /answer <user_id> <javob matni>\n"
            "Misol: /answer 123456789 Salom! Sizning savolingizga javob..."
        )
        return

    try:
        user_id = int(parts[0])
        reply_text = parts[1]
    except ValueError:
        await message.answer("❌ user_id raqam bo'lishi kerak.")
        return

    try:
        await message.bot.send_message(chat_id=user_id, text=reply_text)
        await message.answer(f"✅ Javob foydalanuvchiga (ID: {user_id}) yuborildi.")
    except Exception as e:
        logger.exception(f"Error sending reply to user {user_id}: {e}")
        await message.answer(
            f"❌ Xatolik: Foydalanuvchiga javob yuborib bo'lmadi.\n"
            f"Ehtimol foydalanuvchi botni bloklagan yoki ID noto'g'ri."
        )


@router.message(Command("support_tickets"))
async def cmd_support_tickets(message: Message):
    """Show last support tickets for admin."""
    if message.chat.id != ADMIN_ID:
        return

    try:
        tickets = get_support_tickets(limit=5)
        if not tickets:
            await message.answer("📨 Support so'rovlar topilmadi.")
            return

        text = "📨 Oxirgi support so'rovlar:\n\n"
        for ticket in tickets:
            text += (
                f"🎫 Ticket #{ticket[0]}\n"
                f"👤 User: @{ticket[2] or 'N/A'} (ID: {ticket[1]})\n"
                f"📂 Kategoriya: {ticket[3]}\n"
                f"❓ Savol: {ticket[4][:50]}...\n"
                f"⏰ {ticket[6]}\n\n"
            )
        await message.answer(text)
    except Exception as e:
        logger.exception(f"Error getting support tickets: {e}")
        await message.answer("❌ Xatolik: Support so'rovlarni olishda muammo.")
