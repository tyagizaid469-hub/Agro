"""
run.py — Entry point for Argo Search Bot
"""

import os
import sys
import asyncio
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def check_env():
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID    = os.getenv("API_ID", "0")
    API_HASH  = os.getenv("API_HASH", "")

    missing = []
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        missing.append("BOT_TOKEN")
    if API_ID == "0" or not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")

    if missing:
        logger.error("❌ Missing environment variables:")
        for var in missing:
            logger.error(f"   → {var} is not set!")
        sys.exit(1)

    logger.info("✅ Environment variables OK")


async def run():
    from database import SearchDatabase
    from search_engine import SearchEngine
    from telegram_scraper import TelegramScraper
    import bot as bot_module

    # Init DB
    db = SearchDatabase()
    logger.info("✅ Database ready")

    # Init Telethon scraper
    logger.info("🔌 Connecting to Telegram API (Telethon)...")
    scraper = TelegramScraper(db)
    await scraper.start()
    logger.info("✅ Telethon connected — real Telegram search enabled!")

    # Init SearchEngine
    engine = SearchEngine(db, scraper=scraper)
    logger.info("✅ Search engine ready")

    # Inject dependencies into bot module globals
    bot_module.db      = db
    bot_module.engine  = engine
    bot_module.scraper = scraper

    # Start bot — NO arguments
    await bot_module.main()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════╗
║       🔍 ARGO SEARCH BOT            ║
║   Real Telegram Search Engine       ║
╚══════════════════════════════════════╝
    """)

    check_env()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
