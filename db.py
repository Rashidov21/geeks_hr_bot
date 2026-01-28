"""
Database utilities for HR Bot (SQLite + context manager)
"""
import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Dict, Any


DB_PATH = "hr_bot.db"


@contextmanager
def db_connection():
    """
    Database connection context manager.
    Ensures proper connection handling and cleanup.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def ensure_db() -> None:
    """
    Create database table if it doesn't exist.
    Add missing columns if needed for backward compatibility.
    """
    try:
        with db_connection() as conn:
            c = conn.cursor()
            # Create table if not exists
            c.execute(
                """
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
            """
            )
            
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
                        if col == "created_at":
                            c.execute(f"ALTER TABLE applicants ADD COLUMN {col} {coltype}")
                        else:
                            c.execute(f"ALTER TABLE applicants ADD COLUMN {col} TEXT")
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.exception(f"Cannot add column {col}: {e}")
            
            conn.commit()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error initializing database: {e}")
        raise


def save_application(data: Dict[str, Any]) -> int:
    """
    Insert new application and return inserted id.
    
    Args:
        data: Dictionary containing application data
    
    Returns:
        Inserted row ID
    """
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO applicants
            (name, age, phone, vacancy, subject, experience, workplace, username, photo_id, cv_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("name"),
                data.get("age"),
                data.get("phone"),
                data.get("vacancy"),
                data.get("subject"),
                data.get("experience"),
                data.get("workplace"),
                data.get("username"),
                data.get("photo_id"),
                data.get("cv_file_id"),
            ),
        )
        conn.commit()
        return c.lastrowid


def get_last_applicants(limit: int = 5, vacancy: str | None = None) -> List[Tuple]:
    """
    Return last N applicants, optionally filtered by vacancy.
    
    Args:
        limit: Maximum number of records to return
        vacancy: Filter by vacancy (optional)
    
    Returns:
        List of applicant records
    """
    with db_connection() as conn:
        c = conn.cursor()
        if vacancy:
            c.execute(
                """
                SELECT name, phone, vacancy, subject, experience, workplace
                FROM applicants
                WHERE vacancy=?
                ORDER BY id DESC
                LIMIT ?
            """,
                (vacancy, limit),
            )
        else:
            c.execute(
                """
                SELECT name, phone, vacancy, subject, experience, workplace
                FROM applicants
                ORDER BY id DESC
                LIMIT ?
            """,
                (limit,),
            )
        return c.fetchall()


def get_all_applicants(vacancy: str | None = None) -> List[Tuple]:
    """
    Return all applicants, optionally filtered by vacancy.
    
    Args:
        vacancy: Filter by vacancy (optional)
    
    Returns:
        List of all applicant records
    """
    with db_connection() as conn:
        c = conn.cursor()
        if vacancy:
            c.execute("SELECT * FROM applicants WHERE vacancy=?", (vacancy,))
        else:
            c.execute("SELECT * FROM applicants")
        return c.fetchall()
