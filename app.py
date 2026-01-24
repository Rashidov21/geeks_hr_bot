"""
Geeks Andijan HR Bot
Telegram bot for job applications management
"""
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import sqlite3
import openpyxl
import os
import threading
import time
import traceback
import logging
import re
from contextlib import contextmanager
from typing import Dict, Optional, List, Tuple, Any
from config import TOKEN, ADMIN_ID, GROUP_ID, SESSION_TIMEOUT, WEBHOOK_SECRET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if running in webhook mode
WEBHOOK_MODE = os.environ.get('WEBHOOK_MODE', '').lower() == 'true'

# Only import MessageLoop if not in webhook mode (to avoid conflicts)
if not WEBHOOK_MODE:
    from telepot.loop import MessageLoop

# Initialize bot and Flask app
bot = telepot.Bot(TOKEN)
app = Flask(__name__)

# User sessions with TTL
users: Dict[int, Dict[str, Any]] = {}
user_timeouts: Dict[int, float] = {}

# Constants
VACANCIES = ["Sotuvchi", "Admin", "Mentor", "Support"]
MENTOR_SUBJECTS = ["SMM", "Mobilografiya", "Dasturlash"]

# Lock for thread-safe operations
users_lock = threading.Lock()


# === UTILITY FUNCTIONS ===

@contextmanager
def db_connection():
    """
    Database connection context manager.
    Ensures proper connection handling and cleanup.
    """
    conn = None
    try:
        conn = sqlite3.connect("hr_bot.db", timeout=10)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Database error: %s", e)
        raise
    finally:
        if conn:
            conn.close()


def cleanup_old_users() -> None:
    """
    Remove expired user sessions to prevent memory leaks.
    """
    current_time = time.time()
    with users_lock:
        expired = [
            uid for uid, timeout in user_timeouts.items()
            if current_time > timeout
        ]
        for uid in expired:
            users.pop(uid, None)
            user_timeouts.pop(uid, None)
            logger.debug(f"Cleaned up expired session for user {uid}")


def update_user_timeout(chat_id: int) -> None:
    """
    Update user session timeout.
    """
    with users_lock:
        user_timeouts[chat_id] = time.time() + SESSION_TIMEOUT


def get_user(chat_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user session data.
    """
    cleanup_old_users()
    with users_lock:
        return users.get(chat_id)


def set_user(chat_id: int, data: Dict[str, Any]) -> None:
    """
    Set user session data and update timeout.
    """
    with users_lock:
        users[chat_id] = data
        update_user_timeout(chat_id)


def delete_user(chat_id: int) -> None:
    """
    Delete user session.
    """
    with users_lock:
        users.pop(chat_id, None)
        user_timeouts.pop(chat_id, None)


# === VALIDATION FUNCTIONS ===

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    Supports international format with or without + sign.
    """
    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's a valid phone number (7-15 digits, optionally starting with +)
    pattern = r'^\+?[1-9]\d{6,14}$'
    return bool(re.match(pattern, cleaned))


def validate_age(age_str: str) -> Tuple[bool, Optional[int]]:
    """
    Validate age input.
    Returns (is_valid, age_value).
    """
    try:
        age = int(age_str.strip())
        if 16 <= age <= 100:
            return True, age
        return False, None
    except ValueError:
        return False, None


def validate_name(name: str) -> bool:
    """
    Validate name input (non-empty, reasonable length).
    """
    name = name.strip()
    return 2 <= len(name) <= 100 and name.replace(' ', '').isalnum()


def validate_vacancy(vacancy: str) -> bool:
    """
    Validate vacancy name.
    """
    return vacancy in VACANCIES


def validate_subject(subject: str) -> bool:
    """
    Validate mentor subject.
    """
    return subject in MENTOR_SUBJECTS


# === DATABASE FUNCTIONS ===

def ensure_db() -> None:
    """
    Create database table if it doesn't exist.
    Add missing columns if needed for backward compatibility.
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
            # Create table if not exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS applicants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age TEXT,
                    phone TEXT,
                    vacancy TEXT NOT NULL,
                    subject TEXT,
                    experience TEXT,
                    workplace TEXT,
                    username TEXT,
                    photo_id TEXT,
                    cv_file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check and add missing columns
            c.execute("PRAGMA table_info(applicants)")
            existing_cols = {row[1] for row in c.fetchall()}
            
            needed_cols = {
                "name": "TEXT",
                "age": "TEXT",
                "phone": "TEXT",
                "vacancy": "TEXT",
                "subject": "TEXT",
                "experience": "TEXT",
                "workplace": "TEXT",
                "username": "TEXT",
                "photo_id": "TEXT",
                "cv_file_id": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
            for col, coltype in needed_cols.items():
                if col not in existing_cols:
                    try:
                        logger.info(f"Adding missing column `{col}` to applicants")
                        if col == "created_at":
                            c.execute(f"ALTER TABLE applicants ADD COLUMN {col} {coltype}")
                        else:
                            c.execute(f"ALTER TABLE applicants ADD COLUMN {col} TEXT")
                    except Exception as e:
                        logger.exception("Cannot add column %s: %s", col, e)
            
            conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.exception("Error initializing database: %s", e)
        raise


def get_applicants(limit: int = 5, vacancy: Optional[str] = None) -> List[Tuple]:
    """
    Get applicants from database.
    
    Args:
        limit: Maximum number of records to return
        vacancy: Filter by vacancy (optional)
    
    Returns:
        List of applicant records
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
            if vacancy and validate_vacancy(vacancy):
                c.execute("""
                    SELECT name, phone, vacancy, subject, experience, workplace 
                    FROM applicants 
                    WHERE vacancy=? 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (vacancy, limit))
            else:
                c.execute("""
                    SELECT name, phone, vacancy, subject, experience, workplace 
                    FROM applicants 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (limit,))
            return c.fetchall()
    except Exception as e:
        logger.exception("Error fetching applicants: %s", e)
        return []


def get_all_applicants(vacancy: Optional[str] = None) -> List[Tuple]:
    """
    Get all applicants from database.
    
    Args:
        vacancy: Filter by vacancy (optional)
    
    Returns:
        List of all applicant records
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
            if vacancy and validate_vacancy(vacancy):
                c.execute("SELECT * FROM applicants WHERE vacancy=?", (vacancy,))
            else:
                c.execute("SELECT * FROM applicants")
            return c.fetchall()
    except Exception as e:
        logger.exception("Error fetching all applicants: %s", e)
        return []


def save_application(user_data: Dict[str, Any]) -> bool:
    """
    Save application to database.
    
    Args:
        user_data: Dictionary containing application data
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO applicants 
                (name, age, phone, vacancy, subject, experience, workplace, username, photo_id, cv_file_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data.get("name"),
                user_data.get("age"),
                user_data.get("phone"),
                user_data.get("vacancy"),
                user_data.get("subject"),
                user_data.get("experience"),
                user_data.get("workplace"),
                user_data.get("username"),
                user_data.get("photo_id"),
                user_data.get("cv_file_id")
            ))
            conn.commit()
            return True
    except Exception as e:
        logger.exception("Error saving application: %s", e)
        return False


def export_to_excel(vacancy: Optional[str] = None) -> Optional[str]:
    """
    Export applicants to Excel file.
    
    Args:
        vacancy: Filter by vacancy (optional)
    
    Returns:
        File path if successful, None otherwise
    """
    try:
        rows = get_all_applicants(vacancy)
        if not rows:
            return None
        
        if vacancy:
            file_name = f"{vacancy}_arizalar.xlsx"
        else:
            file_name = "all_arizalar.xlsx"
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Arizalar"
        
        # Headers
        headers = ["ID", "Ism", "Yosh", "Telefon", "Vakansiya", "Yo'nalish", 
                   "Tajriba", "Ish joyi", "Username", "Rasm", "CV", "Sana"]
        ws.append(headers)
        
        # Data
        for row in rows:
            ws.append(row)
        
        wb.save(file_name)
        return file_name
    except Exception as e:
        logger.exception("Error exporting to Excel: %s", e)
        return None


# === MESSAGE SENDING HELPERS ===

def send_with_retry(func, *args, max_retries: int = 3, **kwargs) -> bool:
    """
    Send message with retry mechanism.
    
    Args:
        func: Function to call (e.g., bot.sendMessage)
        *args: Positional arguments
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments
    
    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            func(*args, **kwargs)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                time.sleep(1)
            else:
                logger.exception(f"Failed after {max_retries} attempts: {e}")
                return False
    return False


def send_application_to_admin(user_data: Dict[str, Any]) -> None:
    """
    Send application notification to admin and group.
    
    Args:
        user_data: Dictionary containing application data
    """
    # Build message text
    msg_txt = (
        f"📥 Yangi ariza:\n\n"
        f"👤 Ism: {user_data.get('name')}\n"
        f"📅 Yosh: {user_data.get('age')}\n"
        f"📞 Tel: {user_data.get('phone')}\n"
        f"🏢 Vakansiya: {user_data.get('vacancy')}\n"
    )
    
    if user_data.get("vacancy") == "Mentor":
        msg_txt += f"📚 Yo'nalish: {user_data.get('subject')}\n"
        msg_txt += f"💼 Tajriba: {user_data.get('experience')}\n"
    else:
        msg_txt += f"💼 Tajriba: {user_data.get('experience')}\n"
        msg_txt += f"🏭 Ish joyi: {user_data.get('workplace')}\n"
    
    msg_txt += f"🔗 Username: @{user_data.get('username', 'N/A')}"
    
    # Send to admin and group
    recipients = [ADMIN_ID, GROUP_ID]
    photo_id = user_data.get("photo_id")
    cv_file_id = user_data.get("cv_file_id")
    
    for recipient in recipients:
        try:
            send_with_retry(bot.sendMessage, recipient, msg_txt)
            if photo_id:
                send_with_retry(bot.sendPhoto, recipient, photo_id)
            if cv_file_id:
                send_with_retry(bot.sendDocument, recipient, cv_file_id)
        except Exception as e:
            logger.exception(f"Error sending to {recipient}: {e}")
            if recipient == ADMIN_ID:
                # Try to notify admin about the error
                try:
                    bot.sendMessage(ADMIN_ID, f"❗ Yuborishda xatolik: {str(e)}")
                except:
                    pass


# === CALLBACK HANDLER ===

def on_callback_query(msg: Dict) -> None:
    """
    Handle callback queries from inline keyboards.
    
    Args:
        msg: Callback query message
    """
    try:
        query_id, chat_id, data = telepot.glance(msg, flavor="callback_query")
        
        # Answer callback query
        try:
            bot.answerCallbackQuery(query_id, text="Tanlandi")
        except Exception:
            pass
        
        # Show last applications (admin only)
        if data == "show_last" and chat_id == ADMIN_ID:
            rows = get_applicants(limit=5)
            if rows:
                msg_txt = "📋 Oxirgi arizalar:\n\n"
                for r in rows:
                    msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                send_with_retry(bot.sendMessage, chat_id, msg_txt)
            else:
                send_with_retry(bot.sendMessage, chat_id, "Arizalar topilmadi.")
            return
        
        # Restart bot
        if data == "restart_bot":
            set_user(chat_id, {"step": 0})
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    *[[InlineKeyboardButton(text=vac, callback_data=f"vac_{vac}")] for vac in VACANCIES],
                    [InlineKeyboardButton(text="🔄 Botni qayta boshlash", callback_data="restart_bot")]
                ]
            )
            send_with_retry(bot.sendMessage, chat_id,
                           "🔄 Bot qayta boshlandi. Vakansiyani tanlang:",
                           reply_markup=keyboard)
            return
        
        # Vacancy selection
        if data.startswith("vac_"):
            vacancy = data.split("_", 1)[1]
            if validate_vacancy(vacancy):
                set_user(chat_id, {"vacancy": vacancy, "step": 2})
                send_with_retry(bot.sendMessage, chat_id,
                               f"🏢 Siz tanladingiz: {vacancy}\n\nEndi ism-familiyangizni kiriting:")
            else:
                send_with_retry(bot.sendMessage, chat_id, "❗ Noto'g'ri vakansiya tanlandi.")
            return
        
        # Subject selection (for Mentor)
        elif data.startswith("sub_"):
            subject = data.split("_", 1)[1]
            user = get_user(chat_id)
            if user and validate_subject(subject):
                user["subject"] = subject
                set_user(chat_id, user)
                send_with_retry(bot.sendMessage, chat_id, "💼 Necha yillik tajribangiz bor?")
                user["step"] = 6
                set_user(chat_id, user)
            else:
                send_with_retry(bot.sendMessage, chat_id, "❗ Iltimos, avval vakansiyani tanlang (/start).")
    except Exception as e:
        logger.exception("Error in on_callback_query: %s", e)
        try:
            bot.sendMessage(ADMIN_ID, f"Error in callback handler:\n{traceback.format_exc()}")
        except:
            pass


# === FINISH APPLICATION ===

def finish_application(chat_id: int) -> None:
    """
    Complete and save application.
    
    Args:
        chat_id: User's chat ID
    """
    try:
        user = get_user(chat_id)
        if not user:
            send_with_retry(bot.sendMessage, chat_id,
                           "❗ Ariza topilmadi, iltimos /start bilan qaytadan boshlang.")
            return
        
        # Validate required fields
        if not user.get("name") or not user.get("vacancy"):
            send_with_retry(bot.sendMessage, chat_id,
                           "❗ Ariza to'liq emas. Iltimos, /start bilan qaytadan boshlang.")
            return
        
        # Save to database
        if save_application(user):
            # Send to admin and group
            send_application_to_admin(user)
            
            # Confirm to user
            send_with_retry(bot.sendMessage, chat_id,
                           "✅ Rahmat! Arizangiz qabul qilindi. Tez orada siz bilan bog'lanamiz.")
        else:
            send_with_retry(bot.sendMessage, chat_id,
                           "❗ Arizani saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        
        # Clean up user session
        delete_user(chat_id)
        
    except Exception as e:
        logger.exception("Error in finish_application: %s", e)
        try:
            bot.sendMessage(ADMIN_ID, f"Xato finish_application:\n{traceback.format_exc()}")
            bot.sendMessage(chat_id, "❗ Tizimda xatolik yuz berdi. Adminga xabar yuborildi.")
        except:
            pass


# === CV HANDLER ===

def handle_cv(msg: Dict, chat_id: int) -> None:
    """
    Handle CV file upload or skip.
    
    Args:
        msg: Message containing CV or text
        chat_id: User's chat ID
    """
    try:
        user = get_user(chat_id)
        if not user:
            send_with_retry(bot.sendMessage, chat_id,
                           "❗ Ariza topilmadi. /start orqali qayta boshlang.")
            return
        
        content_type, _, _ = telepot.glance(msg)
        
        if content_type == "document":
            file_id = msg["document"]["file_id"]
            user["cv_file_id"] = file_id
            set_user(chat_id, user)
            send_with_retry(bot.sendMessage, chat_id,
                           "📄 Rahmat! CV faylingiz qabul qilindi. ✅")
            finish_application(chat_id)
        
        elif content_type == "text":
            text = msg["text"].strip().lower()
            if text in ["yo'q", "yoq", "yo'q", "yoq", "нет", "no"]:
                user["cv_file_id"] = None
                set_user(chat_id, user)
                send_with_retry(bot.sendMessage, chat_id,
                               "📌 CV faylisiz arizangiz qabul qilindi. ✅")
                finish_application(chat_id)
            else:
                send_with_retry(bot.sendMessage, chat_id,
                               "❗ Iltimos, CV faylini yuboring yoki 'Yo'q' deb yozing.")
        else:
            send_with_retry(bot.sendMessage, chat_id,
                           "❗ Faqat CV faylini yuboring yoki 'Yo'q' deb yozing.")
    except Exception as e:
        logger.exception("Error in handle_cv: %s", e)
        try:
            bot.sendMessage(ADMIN_ID, f"Xato handle_cv:\n{traceback.format_exc()}")
            bot.sendMessage(chat_id, "❗ Ichki xatolik yuz berdi, adminga xabar yuborildi.")
        except:
            pass


# === MAIN HANDLER ===

def handle(msg: Dict) -> None:
    """
    Main message handler.
    
    Args:
        msg: Incoming message
    """
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        text = msg.get("text") if isinstance(msg, dict) else None
        
        # Handle text messages
        if content_type == "text":
            # START command
            if text == "/start":
                set_user(chat_id, {"step": 0})
                
                if chat_id == ADMIN_ID:
                    # Admin interface
                    reply_keyboard = ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text="📋 Oxirgi arizalar"), KeyboardButton(text="📤 Export")],
                        ],
                        resize_keyboard=True
                    )
                    inline_keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            *[[InlineKeyboardButton(text=vac, callback_data=f"vac_{vac}")] for vac in VACANCIES]
                        ]
                    )
                    send_with_retry(bot.sendMessage, chat_id,
                                   "👋 Admin panel.\nVakansiyani tanlang yoki pastdagi tugmalardan foydalaning:",
                                   reply_markup=reply_keyboard)
                    send_with_retry(bot.sendMessage, chat_id,
                                   "Vakansiyani tanlang:",
                                   reply_markup=inline_keyboard)
                else:
                    # Regular user interface
                    reply_keyboard = ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text="🔄 Botni qayta ishga tushirish")],
                        ],
                        resize_keyboard=True
                    )
                    inline_keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            *[[InlineKeyboardButton(text=vac, callback_data=f"vac_{vac}")] for vac in VACANCIES]
                        ]
                    )
                    send_with_retry(bot.sendMessage, chat_id,
                                   "👋 Assalomu alaykum!\n"
                                   "Men orqali Geeks Andijan o'quv markaziga ish uchun ariza topshirishingiz mumkin.\n\n"
                                   "Vakansiyani tanlang yoki pastdagi tugmani bosing:",
                                   reply_markup=reply_keyboard)
                    send_with_retry(bot.sendMessage, chat_id,
                                   "Vakansiyani tanlang:",
                                   reply_markup=inline_keyboard)
                return
            
            # Admin: /last command
            if isinstance(text, str) and text.startswith("/last") and chat_id == ADMIN_ID:
                parts = text.split()
                vacancy = parts[1].capitalize() if len(parts) > 1 else None
                rows = get_applicants(limit=5, vacancy=vacancy)
                if rows:
                    msg_txt = f"📋 Oxirgi arizalar"
                    if vacancy:
                        msg_txt += f" ({vacancy})"
                    msg_txt += ":\n\n"
                    for r in rows:
                        msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                    send_with_retry(bot.sendMessage, chat_id, msg_txt)
                else:
                    send_with_retry(bot.sendMessage, chat_id,
                                   f"{vacancy or 'Umumiy'} bo'yicha ariza topilmadi.")
                return
            
            # Admin: /export command
            if isinstance(text, str) and text.startswith("/export") and chat_id == ADMIN_ID:
                parts = text.split()
                vacancy = parts[1].capitalize() if len(parts) > 1 else None
                
                file_name = export_to_excel(vacancy=vacancy)
                if file_name:
                    try:
                        with open(file_name, "rb") as f:
                            send_with_retry(bot.sendDocument, chat_id, f)
                        os.remove(file_name)
                    except Exception as e:
                        logger.exception("Error sending Excel file: %s", e)
                        send_with_retry(bot.sendMessage, chat_id,
                                       "❗ Faylni yuborishda xatolik yuz berdi.")
                else:
                    send_with_retry(bot.sendMessage, chat_id,
                                   f"{vacancy or 'Umumiy'} bo'yicha ariza topilmadi.")
                return
            
            # Admin: Last applications button
            if chat_id == ADMIN_ID and text == "📋 Oxirgi arizalar":
                rows = get_applicants(limit=5)
                if rows:
                    msg_txt = "📋 Oxirgi arizalar:\n\n"
                    for r in rows:
                        msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                    send_with_retry(bot.sendMessage, chat_id, msg_txt)
                else:
                    send_with_retry(bot.sendMessage, chat_id, "Arizalar topilmadi.")
                return
            
            # Admin: Export button
            if chat_id == ADMIN_ID and text == "📤 Export":
                file_name = export_to_excel()
                if file_name:
                    try:
                        with open(file_name, "rb") as f:
                            send_with_retry(bot.sendDocument, chat_id, f)
                        os.remove(file_name)
                    except Exception as e:
                        logger.exception("Error sending Excel file: %s", e)
                        send_with_retry(bot.sendMessage, chat_id,
                                       "❗ Faylni yuborishda xatolik yuz berdi.")
                else:
                    send_with_retry(bot.sendMessage, chat_id, "Arizalar topilmadi.")
                return
            
            # User: Restart button
            if text == "🔄 Botni qayta ishga tushirish":
                set_user(chat_id, {"step": 0})
                reply_keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🔄 Botni qayta ishga tushirish")],
                    ],
                    resize_keyboard=True
                )
                inline_keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        *[[InlineKeyboardButton(text=vac, callback_data=f"vac_{vac}")] for vac in VACANCIES]
                    ]
                )
                send_with_retry(bot.sendMessage, chat_id,
                               "🔄 Bot qayta boshlandi. Vakansiyani tanlang:",
                               reply_markup=reply_keyboard)
                send_with_retry(bot.sendMessage, chat_id,
                               "Vakansiyani tanlang:",
                               reply_markup=inline_keyboard)
                return
            
            # Step-by-step form processing
            user = get_user(chat_id)
            if user:
                step = user.get("step")
                
                # Step 2: Name
                if step == 2:
                    if not validate_name(text):
                        send_with_retry(bot.sendMessage, chat_id,
                                       "❗ Iltimos, to'g'ri ism-familiya kiriting (2-100 belgi).")
                        return
                    user["name"] = text.strip()
                    user["username"] = msg["from"].get("username", "N/A")
                    user["step"] = 3
                    set_user(chat_id, user)
                    send_with_retry(bot.sendMessage, chat_id, "📅 Yoshni kiriting:")
                    return
                
                # Step 3: Age
                if step == 3:
                    is_valid, age = validate_age(text)
                    if not is_valid:
                        send_with_retry(bot.sendMessage, chat_id,
                                       "❗ Iltimos, to'g'ri yosh kiriting (16-100).")
                        return
                    user["age"] = str(age)
                    user["step"] = 4
                    set_user(chat_id, user)
                    send_with_retry(bot.sendMessage, chat_id, "📞 Telefon raqamingizni yuboring:")
                    return
                
                # Step 4: Phone
                if step == 4:
                    if not validate_phone(text):
                        send_with_retry(bot.sendMessage, chat_id,
                                       "❗ Iltimos, to'g'ri telefon raqam kiriting.\n"
                                       "Misol: +998901234567 yoki 998901234567")
                        return
                    user["phone"] = text.strip()
                    set_user(chat_id, user)
                    
                    if user["vacancy"] == "Mentor":
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[[InlineKeyboardButton(text=sub, callback_data=f"sub_{sub}")]
                                           for sub in MENTOR_SUBJECTS]
                        )
                        send_with_retry(bot.sendMessage, chat_id,
                                       "📚 Qaysi yo'nalishda dars bera olasiz?",
                                       reply_markup=keyboard)
                    else:
                        user["step"] = 6
                        set_user(chat_id, user)
                        send_with_retry(bot.sendMessage, chat_id,
                                       "💼 Necha yillik tajribangiz bor?")
                    return
                
                # Step 6: Experience
                if step == 6:
                    user["experience"] = text.strip()
                    set_user(chat_id, user)
                    
                    if user["vacancy"] == "Mentor":
                        user["step"] = 7
                        set_user(chat_id, user)
                        send_with_retry(bot.sendMessage, chat_id,
                                       "🖼 Iltimos, o'z rasmingizni yuboring:")
                    else:
                        user["step"] = 5.5
                        set_user(chat_id, user)
                        send_with_retry(bot.sendMessage, chat_id,
                                       "🏭 Oldin qayerda ishlagansiz?")
                    return
                
                # Step 5.5: Workplace (for non-Mentor)
                if step == 5.5:
                    user["workplace"] = text.strip()
                    user["step"] = 7
                    set_user(chat_id, user)
                    send_with_retry(bot.sendMessage, chat_id,
                                   "🖼 Iltimos, o'z rasmingizni yuboring:")
                    return
        
        # Handle photo
        if content_type == "photo" and chat_id in users:
            user = get_user(chat_id)
            if user and user.get("step") == 7:
                photo_id = msg["photo"][-1]["file_id"]
                user["photo_id"] = photo_id
                user["step"] = 8
                set_user(chat_id, user)
                send_with_retry(bot.sendMessage, chat_id,
                               "📄 Agar sizda CV (Rezyume) fayl bo'lsa, yuboring (PDF/DOCX).\n"
                               "Aks holda 'Yo'q' deb yozing.")
                return
            elif user and user.get("step") == 8:
                send_with_retry(bot.sendMessage, chat_id,
                               "❗ Iltimos, CV faylini yuboring yoki 'Yo'q' deb yozing.")
                return
        
        # Handle CV (step 8)
        user = get_user(chat_id)
        if user and user.get("step") == 8:
            handle_cv(msg, chat_id)
            return
        
    except Exception as e:
        logger.exception("Error in main handler: %s", e)
        try:
            bot.sendMessage(ADMIN_ID, f"Xato main handler:\n{traceback.format_exc()}")
        except:
            pass


# === FLASK WEBHOOK ROUTES ===

def verify_webhook_secret(request) -> bool:
    """
    Verify webhook request if secret is configured.
    
    Args:
        request: Flask request object
    
    Returns:
        True if valid or no secret configured, False otherwise
    """
    if not WEBHOOK_SECRET:
        return True  # No secret configured, allow all
    
    # Check for secret in headers or query params
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token') or request.args.get('secret')
    return secret == WEBHOOK_SECRET


@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    """
    Webhook endpoint for receiving Telegram updates.
    """
    try:
        # Verify webhook secret if configured
        if not verify_webhook_secret(request):
            logger.warning("Unauthorized webhook request")
            return "Unauthorized", 401
        
        update = request.get_json()
        if update:
            # Handle callback queries
            if 'callback_query' in update:
                on_callback_query(update['callback_query'])
            # Handle regular messages
            elif 'message' in update:
                handle(update['message'])
        return "ok"
    except Exception as e:
        logger.exception("Error in webhook handler: %s", e)
        return "error", 500


@app.route('/')
def index():
    """
    Health check endpoint.
    """
    return "Geeks Andijan HR Bot ishlamoqda..."


@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """
    Set webhook URL endpoint.
    Usage: /setwebhook?url=https://hrbot.geeksandijan.uz/TOKEN
    """
    try:
        webhook_url = request.args.get('url')
        if not webhook_url:
            return ("Please provide ?url= parameter with your full webhook URL "
                   "(e.g., https://yourdomain.com/TOKEN)")
        
        # Delete existing webhook first
        try:
            bot.setWebhook('')
            logger.info("Deleted existing webhook")
        except Exception as e:
            logger.warning(f"Could not delete existing webhook: {e}")
        
        # Set new webhook
        result = bot.setWebhook(webhook_url)
        if result:
            return (f"✅ Webhook set successfully to: {webhook_url}<br>"
                   f"Bot is ready to receive updates via webhook.")
        else:
            return "❌ Failed to set webhook. Check logs for details."
    except Exception as e:
        logger.exception("Error setting webhook: %s", e)
        return f"❌ Error: {str(e)}", 500


@app.route('/deletewebhook', methods=['GET'])
def delete_webhook():
    """
    Delete webhook endpoint.
    """
    try:
        result = bot.setWebhook('')
        if result:
            return "✅ Webhook deleted successfully"
        else:
            return "❌ Failed to delete webhook"
    except Exception as e:
        logger.exception("Error deleting webhook: %s", e)
        return f"❌ Error: {str(e)}", 500


@app.route('/webhookinfo', methods=['GET'])
def webhook_info():
    """
    Get webhook information endpoint.
    """
    try:
        info = bot.getWebhookInfo()
        if info:
            return f"""
            <h3>Webhook Information:</h3>
            <p><strong>URL:</strong> {info.get('url', 'Not set')}</p>
            <p><strong>Pending Updates:</strong> {info.get('pending_update_count', 0)}</p>
            <p><strong>Last Error Date:</strong> {info.get('last_error_date', 'N/A')}</p>
            <p><strong>Last Error Message:</strong> {info.get('last_error_message', 'None')}</p>
            """
        else:
            return "Could not retrieve webhook info"
    except Exception as e:
        logger.exception("Error getting webhook info: %s", e)
        return f"❌ Error: {str(e)}", 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        # Check database connection
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM applicants")
            count = c.fetchone()[0]
        
        return {
            "status": "healthy",
            "database": "connected",
            "applicants_count": count,
            "active_sessions": len(users)
        }
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}, 500


# === LOCAL TEST ===

def run_polling() -> None:
    """
    Run bot in polling mode (for local testing only).
    """
    if WEBHOOK_MODE:
        logger.error("Cannot run polling mode when webhook is active!")
        return
    
    from telepot.loop import MessageLoop
    MessageLoop(bot, {"chat": handle, "callback_query": on_callback_query}).run_as_thread()
    logger.info("🤖 Bot polling rejimida ishlamoqda...")
    while True:
        time.sleep(10)


if __name__ == "__main__":
    ensure_db()
    if WEBHOOK_MODE:
        # Webhook mode - Flask will handle requests
        logger.info("🤖 Bot webhook rejimida ishlamoqda...")
        logger.info("⚠️  Make sure webhook is set! Visit /setwebhook?url=YOUR_URL")
        app.run(host="0.0.0.0", port=5000)
    else:
        # Polling mode for local testing
        # Delete any existing webhook first
        try:
            bot.setWebhook('')
            logger.info("Deleted existing webhook for polling mode")
        except Exception as e:
            logger.warning(f"Could not delete webhook: {e}")
        run_polling()
