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
GROUP_ID: int = int(os.getenv("GROUP_ID", "0"))
SUPPORT_GROUP_ID: int = int(os.getenv("SUPPORT_GROUP_ID", "0"))

# Application Settings
SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "https://hrbot.geeksandijan.uz")
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", f"/{TOKEN}") if TOKEN else "/"
WEBHOOK_URL: str = WEBHOOK_HOST + WEBHOOK_PATH
WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")

WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")  # aiogram server host
WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "8004"))  # aiogram server port

# Validate required configuration
if not TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID must be set in .env file")

if not GROUP_ID:
    raise ValueError("GROUP_ID must be set in .env file")

# SUPPORT_GROUP_ID is optional, defaults to GROUP_ID if not set
if not SUPPORT_GROUP_ID:
    SUPPORT_GROUP_ID = GROUP_ID
