"""
Configuration module for HR Bot (aiogram version)
Loads configuration from environment variables or .env file
"""
import os
from typing import Optional

try:
    from dotenv import load_dotenv

    try:
        load_dotenv(encoding="utf-8")
    except UnicodeDecodeError:
        import warnings

        warnings.warn(
            "Could not read .env file with UTF-8 encoding. Using environment variables only."
        )
        try:
            load_dotenv(encoding="utf-16")
        except Exception:
            pass
except ImportError:
    import warnings

    warnings.warn("python-dotenv not installed. Using environment variables only.")

# Telegram Bot Configuration
TOKEN: str = os.getenv("BOT_TOKEN")  # no default!
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
# Ko'p admin ID'lar (vergul bilan ajratilgan)
ADMIN_IDS_STR: str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = []
if ADMIN_IDS_STR:
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]
# Agar ADMIN_IDS bo'sh bo'lsa, eski ADMIN_ID ni qo'shamiz
if ADMIN_ID and ADMIN_ID not in ADMIN_IDS:
    ADMIN_IDS.append(ADMIN_ID)
# Agar ADMIN_IDS bo'sh bo'lsa va ADMIN_ID ham bo'lsa, uni asosiy admin qilamiz
if not ADMIN_IDS and ADMIN_ID:
    ADMIN_IDS = [ADMIN_ID]

GROUP_ID: int = int(os.getenv("GROUP_ID", "0"))
SUPPORT_GROUP_ID: int = int(os.getenv("SUPPORT_GROUP_ID", "0"))

# Application Settings
SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "https://hrbot.geeksandijan.uz")
# WEBHOOK_PATH: .env dan olsa ishlatiladi, aks holda TOKEN dan yaratiladi
WEBHOOK_PATH_ENV: str = os.getenv("WEBHOOK_PATH", "")
WEBHOOK_PATH: str = WEBHOOK_PATH_ENV if WEBHOOK_PATH_ENV else (f"/{TOKEN}" if TOKEN else "/")
WEBHOOK_URL: str = WEBHOOK_HOST + WEBHOOK_PATH
WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")

# Timezone configuration (default: UTC+5 for Uzbekistan)
TIMEZONE_OFFSET: int = int(os.getenv("TIMEZONE_OFFSET", "5"))  # UTC+5

WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")  # aiogram server host
WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "8004"))  # aiogram server port

# Validate required configuration
if not TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")

if not ADMIN_IDS:
    if ADMIN_ID and ADMIN_ID != 0:
        # Fallback to single ADMIN_ID if ADMIN_IDS is empty
        ADMIN_IDS = [ADMIN_ID]
    else:
        raise ValueError("ADMIN_ID or ADMIN_IDS must be set in .env file (and not 0)")

if not GROUP_ID or GROUP_ID == 0:
    raise ValueError("GROUP_ID must be set in .env file (and not 0)")

# SUPPORT_GROUP_ID is optional, defaults to GROUP_ID if not set
if not SUPPORT_GROUP_ID:
    SUPPORT_GROUP_ID = GROUP_ID


def is_admin(chat_id: int) -> bool:
    """Check if chat_id is in admin list."""
    return chat_id in ADMIN_IDS
