"""
Aiogram-based HR + Support Bot with SQLite and webhook support.
Run this file with: python bot_aiogram.py
"""

import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties

from config import (
    TOKEN,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBAPP_HOST,
    WEBAPP_PORT,
    WEBHOOK_SECRET,
)
from db import ensure_db

# Import routers
from handlers.admin import router as admin_router
from handlers.hr import router as hr_router
from handlers.courses import router as courses_router
from handlers.support import router as support_router
from handlers.common import router as common_router

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("geeks_bot")

# ==========================
#   BOT & DISPATCHER
# ==========================

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Register routers in priority order
# Admin first (highest priority), then HR, Courses, Support, Common last (FAQ fallback)
dp.include_router(admin_router)
dp.include_router(hr_router)
dp.include_router(courses_router)
dp.include_router(support_router)
dp.include_router(common_router)  # FAQ and general handlers last

# ==========================
#   WEBHOOK SERVER (aiohttp)
# ==========================


async def on_startup(app: web.Application):
    """Initialize database and set webhook on startup."""
    ensure_db()
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message", "callback_query", "edited_message", "channel_post"],
    )
    logger.info(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    """Cleanup on shutdown."""
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app() -> web.Application:
    """Create aiohttp application with webhook handler."""
    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Optional health endpoint
    async def health(request: web.Request):
        return web.json_response({"status": "ok"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    return app


async def main():
    """Main entry point."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    logger.info(f"Starting webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}")
    await site.start()

    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
