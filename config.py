"""
Configuration module for HR Bot
Loads configuration from environment variables or .env file
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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