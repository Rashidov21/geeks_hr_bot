"""
Configuration module for HR Bot
Loads configuration from environment variables or .env file
"""
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    # Try to load .env file with error handling
    try:
        load_dotenv(encoding='utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try to detect encoding or skip .env file
        import warnings
        warnings.warn("Could not read .env file with UTF-8 encoding. Using environment variables only.")
        # Try alternative encodings
        try:
            load_dotenv(encoding='utf-16')
        except:
            pass
except ImportError:
    # If dotenv is not installed, continue with environment variables only
    import warnings
    warnings.warn("python-dotenv not installed. Using environment variables only.")

# Telegram Bot Configuration
TOKEN: str = os.getenv("BOT_TOKEN", "8423618425:AAGslrdY8jGmiHdEt65dyoUkWWwU8roORjE")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "668618297"))
GROUP_ID: int = int(os.getenv("GROUP_ID", "-4946035687"))

# Application Settings
SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour in seconds
WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")  # Optional webhook secret for security

# Validate required configuration
if not TOKEN or TOKEN == "your_bot_token_here":
    raise ValueError("BOT_TOKEN must be set in environment variables or .env file")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID must be set in environment variables or .env file")