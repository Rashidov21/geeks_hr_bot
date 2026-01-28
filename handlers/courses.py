"""
Courses information handlers - Course info and lead collection
"""
import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import GROUP_ID
from db import save_course_lead
from handlers.utils import validate_phone

logger = logging.getLogger(__name__)

router = Router()

# Courses data
COURSES = {
    "SMM": {
        "duration": "3 oy",
        "price_info": "Narx menejer orqali",
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Yo'q",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Mavjud",
            },
        },
    },
    "Mobilografiya": {
        "duration": "3 oy",
        "price_info": "Narx menejer orqali",
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Yo'q",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Mavjud",
            },
        },
    },
    "Computer Science": {
        "duration": "3 oy",
        "price_info": "Oyiga 800 000 so'm",
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Yo'q",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Mavjud",
            },
        },
    },
    "Fullstack dasturlash": {
        "duration": "14 oy",
        "price_info": "Oyiga 800 000 so'm",
        "tariffs": {
            "Standart": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Yo'q",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Intensiv": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Yo'q",
            },
            "Premium": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Mavjud",
            },
        },
    },
}


# FSM States for Courses
class CoursesForm(StatesGroup):
    choosing_course = State()
    choosing_tariff = State()
    asking_phone = State()


@router.callback_query(F.data == "menu_courses")
async def start_courses(callback: CallbackQuery, state: FSMContext):
    """Start courses info flow from main menu."""
    await state.clear()
    await state.set_state(CoursesForm.choosing_course)
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course, callback_data=f"course:{course}")]
            for course in COURSES.keys()
        ]
    )
    
    await callback.message.answer(
        "🧑‍💻 <b>Kurslar haqida ma'lumot</b>\n\n"
        "Qaysi kurs haqida ma'lumot olishni xohlaysiz?",
        reply_markup=inline_kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("course:"))
async def show_course_info(callback: CallbackQuery, state: FSMContext):
    """Show course information and tariffs."""
    course_name = callback.data.split(":", 1)[1]
    if course_name not in COURSES:
        await callback.answer("Noto'g'ri kurs", show_alert=True)
        return
    
    course_data = COURSES[course_name]
    await state.update_data(course_name=course_name)
    await state.set_state(CoursesForm.choosing_tariff)
    
    text = (
        f"📚 <b>{course_name}</b>\n\n"
        f"⏱ Davomiyligi: {course_data['duration']}\n"
        f"💰 {course_data['price_info']}\n\n"
        "Tarifni tanlang:"
    )
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tariff, callback_data=f"tariff:{course_name}:{tariff}")]
            for tariff in course_data["tariffs"].keys()
        ]
    )
    
    await callback.message.answer(text, reply_markup=inline_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def show_tariff_details(callback: CallbackQuery, state: FSMContext):
    """Show tariff details and ask for phone."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Xatolik", show_alert=True)
        return
    
    course_name = parts[1]
    tariff_name = parts[2]
    
    if course_name not in COURSES or tariff_name not in COURSES[course_name]["tariffs"]:
        await callback.answer("Noto'g'ri tarif", show_alert=True)
        return
    
    tariff_data = COURSES[course_name]["tariffs"][tariff_name]
    await state.update_data(tariff=tariff_name)
    
    text = (
        f"📋 <b>{tariff_name} tarif</b>\n\n"
        f"⏱ O'qish muddati: {tariff_data['duration']}\n"
        f"👨‍🏫 Support mentor: {tariff_data['support_mentor']}\n"
        f"📚 Qo'shimcha darslar: {tariff_data['extra_lessons']}\n"
        f"💼 Amaliyot: {tariff_data['practice']}\n"
        f"🎯 Ish bilan ta'minlash: {tariff_data['job_guarantee']}\n\n"
        "Sizga mos tarif va aniq narxlar bo'yicha menejerimiz qo'ng'iroq qilishi uchun "
        "telefon raqamingizni qoldiring:"
    )
    
    await callback.message.answer(text)
    await state.set_state(CoursesForm.asking_phone)
    await callback.answer()


@router.message(CoursesForm.asking_phone)
async def process_course_phone(message: Message, state: FSMContext):
    """Process phone number for course lead."""
    if not validate_phone(message.text):
        await message.answer(
            "❗ Iltimos, to'g'ri telefon raqam kiriting.\n"
            "Misol: +998901234567 yoki 998901234567\n\n"
            "Telefon raqamingizni qoldirmasangiz, biz siz bilan bog'lana olmaymiz."
        )
        return
    
    data = await state.get_data()
    phone = message.text.strip()
    
    try:
        lead_id = save_course_lead({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "course_name": data.get("course_name"),
            "tariff": data.get("tariff"),
            "phone": phone,
        })
        
        logger.info(f"Course lead saved with id {lead_id}")
        
        # Send to group
        lead_text = (
            f"📞 <b>Yangi kurs lead</b>\n\n"
            f"👤 User: @{message.from_user.username or 'N/A'} (ID: {message.from_user.id})\n"
            f"📚 Kurs: {data.get('course_name')}\n"
            f"📋 Tarif: {data.get('tariff')}\n"
            f"📞 Telefon: {phone}"
        )
        
        await message.bot.send_message(chat_id=GROUP_ID, text=lead_text)
        
        await message.answer(
            "✅ Rahmat! Telefon raqamingiz qabul qilindi.\n\n"
            "Menejerimiz tez orada sizga qo'ng'iroq qilib, mos tarif va aniq narxlar "
            "haqida ma'lumot beradi."
        )
        
    except Exception as e:
        logger.exception(f"Error saving course lead: {e}")
        await message.answer(
            "❗ Telefon raqamni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )
    
    await state.clear()
