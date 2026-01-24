"""
Database initialization script
Creates the applicants table if it doesn't exist
"""
import sqlite3
from contextlib import contextmanager


@contextmanager
def db_connection():
    """Database connection context manager."""
    conn = None
    try:
        conn = sqlite3.connect("hr_bot.db", timeout=10)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_db():
    """
    Initialize database and create applicants table.
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
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
            conn.commit()
        print("✅ Database muvaffaqiyatli yaratildi!")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        raise


if __name__ == "__main__":
    init_db()
