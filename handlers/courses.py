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

"""
Kurslar bo‘yicha barcha ma’lumotlar:
- duration, price_info: qisqa info
- description: uzun tavsif (HTML format)
- faq: (savol, javob) juftliklari, umumiy FAQ uchun ham ishlatiladi
- tariffs: tariflar bo‘yicha info
"""

COURSES = {
    "SMM": {
        "duration": "3 oy",
        "price_info": "Narxlar bo'yicha menejer bilan bog'laning",
        "description": (
            "📲 <b>SMM — Social Media Marketing (3 oy)</b>\n\n"
            "Instagram, TikTok va Telegram orqali brend va savdoni o'stirish.\n\n"
            "📝 <b>Kurs tavsifi</b>\n"
            "Ushbu 3 oylik SMM kursi ijtimoiy tarmoqlarda professional sahifa yuritish, "
            "kontent strategiya tuzish va mijoz olib keladigan marketingni o'rgatadi. "
            "Kurs davomida siz Instagram, TikTok va Telegram bilan ishlash, reklama sozlash, "
            "analitika va real loyihalar asosida SMM mutaxassis bo'lib chiqasiz.\n\n"
            "🧭 <b>Kurs tuzilishi (3 oy)</b>\n"
            "📌 1-oy: SMM Asoslari\n"
            "• SMM nima va qanday ishlaydi\n"
            "• Target auditoriyani aniqlash\n"
            "• Profil va sahifa dizayni\n"
            "• Kontent strategiya asoslari\n\n"
            "🎨 2-oy: Kontent va Reklama\n"
            "• Post, Story, Reels g'oyalari\n"
            "• Video kontent va trendlar\n"
            "• Instagram & Facebook reklama\n"
            "• Copywriting (sotuvchi matnlar)\n\n"
            "🚀 3-oy: Analitika va Amaliyot\n"
            "• Statistika va natijani tahlil qilish\n"
            "• Kontent reja (Content Plan)\n"
            "• Mijoz bilan ishlash\n"
            "• Real loyiha va portfolio\n\n"
            "🎯 <b>Kimlar uchun?</b>\n"
            "• SMM va ijtimoiy tarmoqlarda professional sahifa yuritishni o'rganmoqchi bo'lganlar uchun\n"
            "• Biznesi yoki shaxsiy brendini onlayn rivojlantirmoqchi bo'lganlar uchun\n"
            "• SMM orqali masofadan daromad topmoqchi bo'lganlar uchun\n\n"
            "⭐ <b>Kurs afzalliklari</b>\n"
            "• Kurs nol bilimdan boshlab tushuntiriladi\n"
            "• Darslar real loyiha va amaliy topshiriqlar asosida\n"
            "• Reklama va kontent orqali mijoz olib kelish o'rgatiladi\n"
            "• Kurs oxirida portfolio va sertifikat beriladi\n"
        ),
        "faq": [
            ("SMM kursi uchun tajriba kerakmi?", "Yo'q, kurs yangi boshlovchilar uchun mos."),
            ("Qaysi platformalar o'rgatiladi?", "Instagram, TikTok va Telegram bilan ishlanadi."),
            ("Reklama sozlashni ham o'rganamizmi?", "Ha, Instagram va Facebook reklamalari amaliy tarzda o'rgatiladi."),
            ("Kursdan keyin qayerda ishlash mumkin?",
             "Freelancer, SMM menejer yoki biznes sahifasi yurituvchi sifatida ishlash mumkin."),
            ("Sertifikat beriladimi?", "Ha, kursni muvaffaqiyatli tugatganlarga sertifikat beriladi."),
        ],
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topishga yordam beriladi",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topishga yordam beriladi",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topish kafolati mavjud",
            },
        },
    },
    "Mobilografiya": {
        "duration": "3 oy",
        "price_info": "Narxlar bo'yicha menejer bilan bog'laning",
        "description": (
            "📱 <b>Mobilografiya (3 oy)</b>\n\n"
            "Telefon orqali professional video va kontent yaratish.\n\n"
            "📝 <b>Kurs tavsifi</b>\n"
            "Ushbu 3 oylik Mobilografiya kursi telefon orqali professional darajadagi video va foto "
            "kontent yaratishni o'rgatadi. Siz suratga olish, kadr tuzish, yorug'lik bilan ishlash, "
            "montaj va ijtimoiy tarmoqlar uchun kontent tayyorlashni amaliy mashg'ulotlar asosida o'zlashtirasiz.\n\n"
            "🧭 <b>Kurs tuzilishi (3 oy)</b>\n"
            "📸 1-oy: Suratga olish asoslari\n"
            "• Telefon kamerasi sozlamalari\n"
            "• Kadr tuzish va kompozitsiya\n"
            "• Yorug'lik bilan ishlash\n"
            "• Video va foto formatlari\n\n"
            "✂️ 2-oy: Montaj va ishlov berish\n"
            "• CapCut / VN / InShot bilan montaj\n"
            "• Rang, effekt va o'tishlar\n"
            "• Musiqa va ovoz bilan ishlash\n"
            "• Video formatlari (Reels, Shorts, TikTok)\n\n"
            "🚀 3-oy: Kontent va SMM\n"
            "• Instagram, TikTok uchun kontent\n"
            "• Kontent reja tuzish\n"
            "• Trendlar va algoritmlar\n"
            "• Portfolio video va real loyiha\n\n"
            "🎯 <b>Kimlar uchun?</b>\n"
            "• Telefon orqali video va foto olishni professional darajaga olib chiqmoqchi bo'lganlar uchun\n"
            "• SMM, biznes yoki shaxsiy brend uchun sifatli kontent yaratmoqchi bo'lganlar uchun\n"
            "• Kreativ fikrlashni rivojlantirib, mobilografiya orqali daromad topmoqchi bo'lganlar uchun\n\n"
            "⭐ <b>Kurs afzalliklari</b>\n"
            "• Kurs 0 dan boshlanadi va telefon yetarli bo'ladi\n"
            "• Darslar to'liq amaliy mashg'ulotlar asosida o'tiladi\n"
            "• Ijtimoiy tarmoqlar algoritmlariga mos real kontent yaratiladi\n"
            "• Kurs oxirida portfolio va real loyiha bilan chiqiladi\n"
        ),
        "faq": [
            ("Bu kurs uchun professional kamera kerakmi?", "Yo'q, oddiy smartfon yetarli bo'ladi."),
            ("Qaysi ilovalar bilan ishlanadi?", "CapCut, VN, InShot kabi mashhur mobil montaj ilovalari bilan ishlanadi."),
            ("Darslar nazariymi yoki amaliymi?", "Darslar asosan amaliy, har bir mavzu real video orqali o'rganiladi."),
            ("Kurs tugagach nimalarni qila olaman?",
             "Ijtimoiy tarmoqlar uchun professional video va kontent tayyorlay olasiz."),
            ("Kurs yakunida sertifikat beriladimi?", "Ha, kursni muvaffaqiyatli tugatganlarga sertifikat beriladi."),
        ],
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topishga yordam beriladi",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topishga yordam beriladi",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ish topish kafolati mavjud",
            },
        },
    },
    "Python Fullstack dasturlash": {
        "duration": "14 oy",
        "price_info": "Oyiga 800 000 so'm (aniq narxlar menejer orqali)",
        "description": (
            "🐍 <b>Python Fullstack Dasturlash (14 oy)</b>\n\n"
            "0 dan professional web dasturchigacha.\n\n"
            "📝 <b>Kurs tavsifi</b>\n"
            "Ushbu 14 oylik Python Fullstack kursi sizni IT olamiga to'liq olib kirish uchun mo'ljallangan. "
            "Kurs davomida siz frontend va backend dasturlashni bosqichma-bosqich, amaliy mashg'ulotlar asosida "
            "o'rganasiz. HTML, CSS, JavaScript, React, Python, Django, DRF va FastAPI orqali real web loyihalar "
            "yaratishni o'zlashtirasiz.\n\n"
            "🧭 <b>Kurs tuzilishi (14 oy)</b>\n"
            "🎨 Frontend — 7 oy\n"
            "• HTML & CSS – veb sahifalar tuzilishi va dizayni\n"
            "• JavaScript – interaktiv va dinamik funksiyalar\n"
            "• React – zamonaviy va tezkor UI yaratish\n\n"
            "⚙️ Backend — 7 oy\n"
            "• Python asoslari (3 oy) – syntax, OOP, mantiqiy fikrlash\n"
            "• Django (2 oy) – kuchli va xavfsiz backend\n"
            "• DRF & FastAPI (2 oy) – REST API va tezkor backend xizmatlar\n\n"
            "🎯 <b>Kimlar uchun?</b>\n"
            "• Dasturlashni mutlaqo 0 dan boshlamoqchi bo'lganlar\n"
            "• Frontend va backendni birgalikda o'rganib, fullstack dasturchi bo'lishni istaganlar\n"
            "• IT sohasida mustahkam kasb va barqaror daromadga erishmoqchi bo'lganlar\n\n"
            "⭐ <b>Kurs afzalliklari</b>\n"
            "• Kurs boshlang'ichdan professional darajagacha olib boradi\n"
            "• Har bir texnologiya amaliy loyiha va real misollar orqali o'rgatiladi\n"
            "• Frontend + Backend + API + Deploy — to'liq fullstack bilimlar\n"
            "• Kurs oxirida real portfolio loyihalar va sertifikat\n"
        ),
        "faq": [
            ("Bu kurs uchun oldindan dasturlash bilimi kerakmi?",
             "Yo'q, kurs 0 dan boshlanadi va barcha mavzular oddiy tilda tushuntiriladi."),
            ("14 oy davomida nimalarni o'rganaman?",
             "Frontend (HTML, CSS, JS, React), Backend (Python, Django, DRF, FastAPI), Git, API va deploy."),
            ("Darslar amaliymi yoki nazariyami?",
             "Darslar asosan amaliy bo'lib, har bir modulda real loyiha qilinadi."),
            ("Kurs tugagach ish topa olamanmi?",
             "Kurs davomida portfolio yig'iladi, bu esa ish topishda katta ustunlik beradi."),
            ("Kurs yakunida sertifikat beriladimi?",
             "Ha, kursni muvaffaqiyatli yakunlagan o'quvchilarga sertifikat beriladi."),
        ],
        "tariffs": {
            "Standart": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Upwork, Freelancer, Workana va boshqa platformalardan ish topishga yordam beriladi",
            },
            "Intensiv": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Upwork, Freelancer, Workana va boshqa platformalardan ish topishga yordam beriladi",
            },
            "Premium": {
                "duration": "14 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Upwork, Freelancer, Workana va boshqa platformalardan ish topishga yordam beriladi",
            },
        },
    },
    "Computer Science": {
        "duration": "3 oy",
        "price_info": "Narxlar bo'yicha menejer bilan bog'laning",
        "description": (
            "💻 <b>Computer Science (3 oy)</b>\n\n"
            "IT'ga 0 dan kirish va mustahkam poydevor.\n\n"
            "📝 <b>Kurs tavsifi</b>\n"
            "Ushbu 3 oylik Computer Science kursi IT sohasiga butunlay 0 dan kirib kelmoqchi bo'lganlar uchun. "
            "Kompyuter va internet asoslari, Office dasturlari, dizayn, UI/UX va IT mantiqi oddiy va tushunarli "
            "tilda, ko'p amaliyot bilan o'rgatiladi. Bu kurs kelajakda dasturlash, dizayn yoki boshqa IT "
            "yo'nalishlarni o'rganish uchun kuchli start beradi.\n\n"
            "🧭 <b>Kurs tuzilishi (3 oy)</b>\n"
            "🖥 1-oy: Kompyuter va Internet Asoslari\n"
            "• Kompyuter qismlari va ishlash tamoyili\n"
            "• Internet, DNS, IP, brauzerlar\n"
            "• Klaviatura, tezkor tugmalar\n"
            "• Internet xavfsizligi va antivirus\n\n"
            "📄 2-oy: Office va Algoritmik Fikrlash\n"
            "• Microsoft Word (hujjatlar, dizayn)\n"
            "• Excel (jadval, formula, diagramma)\n"
            "• PowerPoint (taqdimotlar)\n"
            "• Algoritm va mantiqiy fikrlash asoslari\n\n"
            "🎨 3-oy: Dizayn va IT Yo'nalishlarga Kirish\n"
            "• Canva, Figma asoslari\n"
            "• UI/UX tushunchalari\n"
            "• IT yo'nalishlar overview (Frontend, Backend, Design)\n"
            "• Yakuniy loyiha va taqdimot\n\n"
            "🎯 <b>Kimlar uchun?</b>\n"
            "• IT sohasiga 0 dan kirib kelmoqchi bo'lganlar\n"
            "• Kompyuter va internetdan samarali foydalanishni o'rganmoqchi bo'lganlar\n"
            "• Kelajakda dasturlash, dizayn yoki boshqa IT yo'nalishlarga poydevor qo'ymoqchi bo'lganlar\n\n"
            "⭐ <b>Kurs afzalliklari</b>\n"
            "• Kurs mutlaqo 0 dan boshlanadi\n"
            "• Nazariya bilan birga ko'p amaliy mashg'ulotlar\n"
            "• Office, dizayn, UI/UX va IT asoslari bitta kursda jamlangan\n"
            "• Kurs oxirida real loyiha ustida ishlanadi\n"
        ),
        "faq": [
            ("Bu kursga qatnashish uchun oldindan bilim kerakmi?",
             "Yo'q, kurs to'liq 0 dan boshlanadi va yangi boshlovchilar uchun mos."),
            ("Kurs davomiyligi qancha?", "Kurs 3 oy davom etadi va haftasiga reja asosida darslar o'tiladi."),
            ("Darslar nazariymi yoki amaliy ham bormi?",
             "Darslar asosan amaliy bo'lib, har bir mavzu mashqlar orqali mustahkamlanadi."),
            ("Kurs tugagach nimalarni bilaman?",
             "Kompyuter va internet asoslari, Office dasturlari, dizayn va UI/UX tushunchalari hamda real loyiha tajribasi."),
            ("Kurs yakunida sertifikat beriladimi?",
             "Ha, kursni muvaffaqiyatli tugatgan talabalarga sertifikat topshiriladi."),
        ],
        "tariffs": {
            "Standart": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ishda kerakli ko'nikmalar o'rganiladi",
            },
            "Intensiv": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ishda kerakli ko'nikmalar o'rganiladi",
            },
            "Premium": {
                "duration": "3 oy",
                "support_mentor": "Mavjud",
                "extra_lessons": "Mavjud",
                "practice": "Mavjud",
                "job_guarantee": "Ishda kerakli ko'nikmalar o'rganiladi",
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
    """Show course information (description + basic info) and tariffs."""
    course_name = callback.data.split(":", 1)[1]
    if course_name not in COURSES:
        await callback.answer("Noto'g'ri kurs", show_alert=True)
        return
    
    course_data = COURSES[course_name]
    await state.update_data(course_name=course_name)
    await state.set_state(CoursesForm.choosing_tariff)
    
    # 1) To‘liq kurs tavsifi (agar berilgan bo‘lsa)
    description = course_data.get("description")
    if description:
        await callback.message.answer(description)
    
    # 2) Qisqa info va tarif tanlash
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
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    contact_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Kontaktni ulashish", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.answer(text, reply_markup=contact_kb)
    await state.set_state(CoursesForm.asking_phone)
    await callback.answer()


@router.message(CoursesForm.asking_phone, F.contact)
async def process_course_phone_contact(message: Message, state: FSMContext):
    """Process phone from contact for course."""
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
        # Add + if not present
        if not phone.startswith('+'):
            phone = '+' + phone
        
        data = await state.get_data()
        
        try:
            from db import save_course_lead
            lead_id = save_course_lead({
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "course_name": data.get("course_name"),
                "tariff": data.get("tariff"),
                "phone": phone,
            })
            logger.info(f"Course lead saved with id {lead_id}")
            
            await message.answer(
                "✅ Rahmat! Telefon raqamingiz qabul qilindi.\n\n"
                "Menejerimiz tez orada siz bilan bog'lanadi va kurs haqida batafsil ma'lumot beradi."
            )
        except Exception as e:
            logger.exception(f"Error saving course lead: {e}")
            await message.answer(
                "❗ Telefon raqamni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
            )
        finally:
            await state.clear()
    else:
        await message.answer("❗ Kontakt ma'lumotlari topilmadi. Iltimos, telefon raqamni qo'lda kiriting.")


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
