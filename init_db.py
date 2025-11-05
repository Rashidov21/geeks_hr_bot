import sqlite3
def init_db():
    conn = sqlite3.connect("hr_bot.db")
    c = conn.cursor()
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
    conn.close()
    print("✅ Yangi jadval muvaffaqiyatli yaratildi!")
init_db()
