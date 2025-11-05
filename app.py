# bot_fixed.py
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import sqlite3, openpyxl, os, threading, time, traceback, logging
from config import TOKEN, ADMIN_ID, GROUP_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running in webhook mode
WEBHOOK_MODE = os.environ.get('WEBHOOK_MODE', '').lower() == 'true'

# Only import MessageLoop if not in webhook mode (to avoid conflicts)
if not WEBHOOK_MODE:
    from telepot.loop import MessageLoop

bot = telepot.Bot(TOKEN)
app = Flask(__name__)

users = {}
VACANCIES = ["Sotuvchi", "Admin", "Mentor", "Support"]
MENTOR_SUBJECTS = ["SMM", "Mobilografiya", "Dasturlash"]


# === DATABASE ===
def db_connect():
    # agar xohlasangiz timeout va check_same_thread parametrlarini qo'shishingiz mumkin
    return sqlite3.connect("hr_bot.db", timeout=10)


def ensure_db():
    """
    Yangi jadval yaratadi agar yo'q bo'lsa, yoki mavjud jadvalga kerakli ustunlarni qo'shadi.
    Bu eski DB'larga moslash uchun.
    """
    conn = db_connect()
    c = conn.cursor()
    # Yangi jadvalni yaratish (agar yo'q bo'lsa)
    c.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            phone TEXT,
            vacancy TEXT,
            subject TEXT,
            experience TEXT,
            workplace TEXT,
            username TEXT,
            photo_id TEXT,
            cv_file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Tekshirib, yetishmayotgan ustunlarni ADD qilamiz
    c.execute("PRAGMA table_info(applicants)")
    cols = [row[1] for row in c.fetchall()]  # row: (cid, name, type, notnull, dflt_value, pk)
    needed = {
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
    for col, coltype in needed.items():
        if col not in cols:
            try:
                logger.info(f"Adding missing column `{col}` to applicants")
                c.execute(f"ALTER TABLE applicants ADD COLUMN {col} {coltype}")
            except Exception:
                # ba'zi SQLite versiyalarda DEFAULT expression bilan ADD qilish muammo bo'lishi mumkin:
                try:
                    # oddiy ADD COLUMN TEXT
                    c.execute(f"ALTER TABLE applicants ADD COLUMN {col} TEXT")
                except Exception as e:
                    logger.exception("Cannot add column %s: %s", col, e)
    conn.commit()
    conn.close()
    logger.info("DB ready")


# === CALLBACK HANDLER ===
def on_callback_query(msg):
    try:
        query_id, chat_id, data = telepot.glance(msg, flavor="callback_query")
        try:
            bot.answerCallbackQuery(query_id, text="Tanlandi")
        except Exception:
            pass

        if data == "show_last" and chat_id == ADMIN_ID:
            conn = db_connect()
            c = conn.cursor()
            c.execute("""SELECT name, phone, vacancy, subject, experience, workplace 
                         FROM applicants ORDER BY id DESC LIMIT 5""")
            rows = c.fetchall()
            conn.close()
            if rows:
                msg_txt = "📋 Oxirgi arizalar:\n\n"
                for r in rows:
                    msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                bot.sendMessage(chat_id, msg_txt)
            else:
                bot.sendMessage(chat_id, "Arizalar topilmadi.")
            return

        if data == "restart_bot":
            users[chat_id] = {"step": 0}
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    *[[InlineKeyboardButton(text=vac, callback_data=f"vac_{vac}")] for vac in VACANCIES],
                    [InlineKeyboardButton(text="🔄 Botni qayta boshlash", callback_data="restart_bot")]
                ]
            )
            bot.sendMessage(chat_id,
                            "🔄 Bot qayta boshlandi. Vakansiyani tanlang:",
                            reply_markup=keyboard)
            return

        if data.startswith("vac_"):
            vacancy = data.split("_", 1)[1]
            users[chat_id] = {"vacancy": vacancy, "step": 2}
            bot.sendMessage(chat_id, f"🏢 Siz tanladingiz: {vacancy}\n\nEndi ism-familiyangizni kiriting:")

        elif data.startswith("sub_"):
            subject = data.split("_", 1)[1]
            if chat_id in users:
                users[chat_id]["subject"] = subject
                bot.sendMessage(chat_id, "💼 Necha yillik tajribangiz bor?")
                users[chat_id]["step"] = 6
            else:
                bot.sendMessage(chat_id, "❗ Iltimos, avval vakansiyani tanlang (/start).")
    except Exception:
        logger.exception("Error in on_callback_query")
        bot.sendMessage(ADMIN_ID, f"Error in callback handler:\n{traceback.format_exc()}")


# === FINISH APPLICATION ===
def finish_application(chat_id):
    try:
        u = users.get(chat_id)
        if not u:
            bot.sendMessage(chat_id, "❗ Ariza topilmadi, iltimos /start bilan qaytadan boshlang.")
            return

        conn = db_connect()
        c = conn.cursor()
        c.execute("""INSERT INTO applicants 
                    (name, age, phone, vacancy, subject, experience, workplace, username, photo_id, cv_file_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            u.get("name"),
            u.get("age"),
            u.get("phone"),
            u.get("vacancy"),
            u.get("subject"),
            u.get("experience"),
            u.get("workplace"),
            u.get("username"),
            u.get("photo_id"),
            u.get("cv_file_id")
        ))
        conn.commit()
        conn.close()

        # HR ga yuborish
        msg_txt = (f"📥 Yangi ariza:\n\n"
                   f"👤 Ism: {u.get('name')}\n"
                   f"📅 Yosh: {u.get('age')}\n"
                   f"📞 Tel: {u.get('phone')}\n"
                   f"🏢 Vakansiya: {u.get('vacancy')}\n")

        if u.get("vacancy") == "Mentor":
            msg_txt += f"📚 Yo‘nalish: {u.get('subject')}\n💼 Tajriba: {u.get('experience')}\n"
        else:
            msg_txt += f"💼 Tajriba: {u.get('experience')}\n🏭 Ish joyi: {u.get('workplace')}\n"

        msg_txt += f"🔗 Username: @{u.get('username')}"

        try:
            # Отправка админу
            bot.sendMessage(ADMIN_ID, msg_txt)
            if u.get("photo_id"):
                bot.sendPhoto(ADMIN_ID, u["photo_id"])
            if u.get("cv_file_id"):
                bot.sendDocument(ADMIN_ID, u["cv_file_id"])
            # Отправка в закрытую группу
            bot.sendMessage(GROUP_ID, msg_txt)
            if u.get("photo_id"):
                bot.sendPhoto(GROUP_ID, u["photo_id"])
            if u.get("cv_file_id"):
                bot.sendDocument(GROUP_ID, u["cv_file_id"])
        except Exception as e:
            logger.exception("Error sending files to admin/group: %s", e)
            bot.sendMessage(ADMIN_ID, "❗ Yuborishda xatolik: fayl yoki rasm yuborilmadi.\n" + str(e))

        bot.sendMessage(chat_id, "✅ Rahmat! Arizangiz qabul qilindi. Tez orada siz bilan bog‘lanamiz.")
        if chat_id in users:
            del users[chat_id]

    except Exception:
        logger.exception("Error in finish_application")
        bot.sendMessage(ADMIN_ID, f"Xato finish_application:\n{traceback.format_exc()}")
        bot.sendMessage(chat_id, "❗ Tizimda xatolik yuz berdi. Adminga xabar yuborildi.")


# === CV HANDLER ===
def handle_cv(msg, chat_id):
    try:
        u = users.get(chat_id)
        if not u:
            bot.sendMessage(chat_id, "❗ Ariza topilmadi. /start orqali qayta boshlang.")
            return

        content_type, _, _ = telepot.glance(msg)

        if content_type == "document":
            file_id = msg["document"]["file_id"]
            u["cv_file_id"] = file_id
            bot.sendMessage(chat_id, "📄 Rahmat! CV faylingiz qabul qilindi. ✅")
            finish_application(chat_id)

        elif content_type == "text":
            text = msg["text"].strip().lower()
            if text in ["yo'q", "yoq", "yo‘q", "yoq"]:
                u["cv_file_id"] = None
                bot.sendMessage(chat_id, "📌 CV faylisiz arizangiz qabul qilindi. ✅")
                finish_application(chat_id)
            else:
                bot.sendMessage(chat_id, "❗ Iltimos, CV faylini yuboring yoki 'Yo‘q' deb yozing.")
        else:
            bot.sendMessage(chat_id, "❗ Faqat CV faylini yuboring yoki 'Yo‘q' deb yozing.")
    except Exception:
        logger.exception("Error in handle_cv")
        bot.sendMessage(ADMIN_ID, f"Xato handle_cv:\n{traceback.format_exc()}")
        bot.sendMessage(chat_id, "❗ Ichki xatolik yuz berdi, adminga xabar yuborildi.")


# === MAIN HANDLER ===
def handle(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)

        # matnli xabarlar uchun text oling (agar mavjud bo'lsa)
        text = msg.get("text") if isinstance(msg, dict) else None

        # TEXT ishini boshlaymiz
        if content_type == "text":
            # START
            if text == "/start":
                users[chat_id] = {"step": 0}
                # ReplyKeyboard для админа
                if chat_id == ADMIN_ID:
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
                    bot.sendMessage(chat_id,
                                    "👋 Admin panel.\nVakansiyani tanlang yoki pastdagi tugmalardan foydalaning:",
                                    reply_markup=reply_keyboard)
                    bot.sendMessage(chat_id,
                                    "Vakansiyani tanlang:",
                                    reply_markup=inline_keyboard)
                else:
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
                    bot.sendMessage(chat_id,
                                    "👋 Assalomu alaykum!\n"
                                    "Men orqali Geeks Andijan o‘quv markaziga ish uchun ariza topshirishingiz mumkin.\n\n"
                                    "Vakansiyani tanlang yoki pastdagi tugmani bosing:",
                                    reply_markup=reply_keyboard)
                    bot.sendMessage(chat_id,
                                    "Vakansiyani tanlang:",
                                    reply_markup=inline_keyboard)
                return

            # ADMIN: oxirgi arizalar
            if isinstance(text, str) and text.startswith("/last") and chat_id == ADMIN_ID:
                parts = text.split()
                if len(parts) == 2:
                    vacancy = parts[1].capitalize()
                    conn = db_connect()
                    c = conn.cursor()
                    c.execute("""SELECT name, phone, vacancy, subject, experience, workplace 
                                 FROM applicants WHERE vacancy=? ORDER BY id DESC LIMIT 5""", (vacancy,))
                    rows = c.fetchall()
                    conn.close()
                    if rows:
                        msg_txt = f"📋 Oxirgi arizalar ({vacancy}):\n\n"
                        for r in rows:
                            msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                        bot.sendMessage(chat_id, msg_txt)
                    else:
                        bot.sendMessage(chat_id, f"{vacancy} bo‘yicha ariza topilmadi.")
                return

            # ADMIN: eksport
            if isinstance(text, str) and text.startswith("/export") and chat_id == ADMIN_ID:
                parts = text.split()
                if len(parts) == 2:
                    vacancy = parts[1].capitalize()
                    conn = db_connect()
                    c = conn.cursor()
                    c.execute("SELECT * FROM applicants WHERE vacancy=?", (vacancy,))
                    rows = c.fetchall()
                    conn.close()

                    if not rows:
                        bot.sendMessage(chat_id, f"{vacancy} bo‘yicha ariza topilmadi.")
                    else:
                        file_name = f"{vacancy}_arizalar.xlsx"
                        wb = openpyxl.Workbook()
                        ws = wb.active
                        ws.title = "Arizalar"
                        ws.append(["ID", "Ism", "Yosh", "Telefon", "Vakansiya", "Yo'nalish", "Tajriba", "Ish joyi",
                                   "Username", "Rasm", "CV", "Sana"])
                        for r in rows:
                            ws.append(r)
                        wb.save(file_name)

                        bot.sendDocument(chat_id, open(file_name, "rb"))
                        os.remove(file_name)
                return

            # ADMIN: обработка reply-кнопок
            if chat_id == ADMIN_ID and text == "📋 Oxirgi arizalar":
                conn = db_connect()
                c = conn.cursor()
                c.execute("""SELECT name, phone, vacancy, subject, experience, workplace 
                             FROM applicants ORDER BY id DESC LIMIT 5""")
                rows = c.fetchall()
                conn.close()
                if rows:
                    msg_txt = "📋 Oxirgi arizalar:\n\n"
                    for r in rows:
                        msg_txt += f"👤 {r[0]} | 📞 {r[1]} | 🏢 {r[2]} | 📚 {r[3]} | 💼 {r[4]} | 🏭 {r[5]}\n\n"
                    bot.sendMessage(chat_id, msg_txt)
                else:
                    bot.sendMessage(chat_id, "Arizalar topilmadi.")
                return

            if chat_id == ADMIN_ID and text == "📤 Export":
                conn = db_connect()
                c = conn.cursor()
                c.execute("SELECT * FROM applicants")
                rows = c.fetchall()
                conn.close()
                if not rows:
                    bot.sendMessage(chat_id, "Arizalar topilmadi.")
                else:
                    file_name = "all_arizalar.xlsx"
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Arizalar"
                    ws.append(["ID", "Ism", "Yosh", "Telefon", "Vakansiya", "Yo'nalish", "Tajriba", "Ish joyi",
                               "Username", "Rasm", "CV", "Sana"])
                    for r in rows:
                        ws.append(r)
                    wb.save(file_name)
                    bot.sendDocument(chat_id, open(file_name, "rb"))
                    os.remove(file_name)
                return

            # USER: обработка reply-кнопки
            if text == "🔄 Botni qayta ishga tushirish":
                users[chat_id] = {"step": 0}
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
                bot.sendMessage(chat_id,
                                "🔄 Bot qayta boshlandi. Vakansiyani tanlang:",
                                reply_markup=reply_keyboard)
                bot.sendMessage(chat_id,
                                "Vakansiyani tanlang:",
                                reply_markup=inline_keyboard)
                return

            # STEP-BY-STEP PROCESS (text inputs)
            if chat_id in users:
                u = users[chat_id]
                step = u.get("step")

                if step == 2:
                    u["name"] = text
                    u["username"] = msg["from"].get("username", "N/A")
                    bot.sendMessage(chat_id, "📅 Yoshni kiriting:")
                    u["step"] = 3
                    return

                if step == 3:
                    u["age"] = text
                    bot.sendMessage(chat_id, "📞 Telefon raqamingizni yuboring:")
                    u["step"] = 4
                    return

                if step == 4:
                    u["phone"] = text
                    if u["vacancy"] == "Mentor":
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[[InlineKeyboardButton(text=sub, callback_data=f"sub_{sub}")]
                                             for sub in MENTOR_SUBJECTS]
                        )
                        bot.sendMessage(chat_id, "📚 Qaysi yo‘nalishda dars bera olasiz?", reply_markup=keyboard)
                        # step will be set when user selects subject (callback)
                    else:
                        bot.sendMessage(chat_id, "💼 Necha yillik tajribangiz bor?")
                        u["step"] = 6
                    return

                if step == 6:
                    u["experience"] = text
                    if u["vacancy"] == "Mentor":
                        bot.sendMessage(chat_id, "🖼 Iltimos, o‘z rasmingizni yuboring:")
                        u["step"] = 7
                    else:
                        bot.sendMessage(chat_id, "🏭 Oldin qayerda ishlagansiz?")
                        u["step"] = 5.5  # maxsus step
                    return

                if step == 5.5:
                    u["workplace"] = text
                    bot.sendMessage(chat_id, "🖼 Iltimos, o‘z rasmingizni yuboring:")
                    u["step"] = 7
                    return

                # Agar step == 8 (CV bosqichi) matn yuborilsa, handle_cv tutib oladi pastda
                # bu funksiya shu yerda tugaydi va pastdagi umumiy CV blokiga o'tadi

        # PHOTO handler (har qanday content_type kelganda tekshiriladi)
        if content_type == "photo" and chat_id in users:
            if users[chat_id].get("step") == 7:
                # Foto qabul qilish
                photo_id = msg["photo"][-1]["file_id"]
                users[chat_id]["photo_id"] = photo_id
                bot.sendMessage(chat_id, "📄 Agar sizda CV (Rezyume) fayl bo‘lsa, yuboring (PDF/DOCX).\n"
                                         "Aks holda 'Yo‘q' deb yozing.")
                users[chat_id]["step"] = 8
                return
            elif users[chat_id].get("step") == 8:
                # Agar foydalanuvchi step==8 da yana photo yuborsa
                bot.sendMessage(chat_id, "❗ Iltimos, CV faylini yuboring yoki 'Yo‘q' deb yozing.")
                return

        # CV: agar foydalanuvchi hozir step==8 da bo'lsa, CV fayl yoki "Yo'q" matni bilan bu yerga tushadi
        if chat_id in users and users[chat_id].get("step") == 8:
            handle_cv(msg, chat_id)
            return

    except Exception:
        # Juda muhim: exceptionni tutamiz va adminga yuboramiz, shunda thread o'lmaydi
        logger.exception("Error in main handler")
        try:
            bot.sendMessage(ADMIN_ID, f"Xato main handler:\n{traceback.format_exc()}")
        except Exception:
            pass


# === FLASK WEBHOOK ===
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
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
    return "Geeks Andijan HR Bot ishlamoqda..."


@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """Set webhook URL - Call this after deploying to set webhook"""
    try:
        webhook_url = request.args.get('url')
        if not webhook_url:
            return "Please provide ?url= parameter with your full webhook URL (e.g., https://yourdomain.com/TOKEN)"
        
        # First, delete any existing webhook to avoid conflicts
        try:
            bot.setWebhook('')
            logger.info("Deleted existing webhook")
        except Exception as e:
            logger.warning(f"Could not delete existing webhook: {e}")
        
        # Set the new webhook
        result = bot.setWebhook(webhook_url)
        if result:
            return f"✅ Webhook set successfully to: {webhook_url}<br>Bot is ready to receive updates via webhook."
        else:
            return f"❌ Failed to set webhook. Check logs for details."
    except Exception as e:
        logger.exception("Error setting webhook: %s", e)
        return f"❌ Error: {str(e)}", 500


@app.route('/deletewebhook', methods=['GET'])
def delete_webhook():
    """Delete webhook - Call this to remove webhook"""
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
    """Get current webhook information"""
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


# === LOCAL TEST ===
def run_polling():
    """Run bot in polling mode (for local testing only)"""
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
        # First, delete any existing webhook to avoid conflicts
        try:
            bot.setWebhook('')
            logger.info("Deleted existing webhook for polling mode")
        except Exception as e:
            logger.warning(f"Could not delete webhook: {e}")
        run_polling()
