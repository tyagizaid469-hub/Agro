"""
run.py — Entry point for Argo Search Bot

Ye file:
1. Environment variables check karta hai
2. Telethon se Telegram login karta hai (pehli baar phone/OTP maangega)
3. Bot start karta hai

Usage:
    python run.py
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


# ── Step 1: Check required environment variables ───────────────────────────────

def check_env():
    missing = []
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID    = os.getenv("API_ID", "0")
    API_HASH  = os.getenv("API_HASH", "")

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
        logger.error("")
        logger.error("📖 Setup karo:")
        logger.error("   export BOT_TOKEN='your_bot_token'")
        logger.error("   export API_ID='12345678'")
        logger.error("   export API_HASH='abcdef...'")
        logger.error("")
        logger.error("   Puri guide: API_SETUP.md")
        sys.exit(1)

    logger.info("✅ Environment variables OK")
    return BOT_TOKEN, int(API_ID), API_HASH


# ── Step 2: Main async runner ─────────────────────────────────────────────────

async def run():
    from database import SearchDatabase
    from search_engine import SearchEngine
    from telegram_scraper import TelegramScraper
    from bot import main as bot_main

    logger.info("🚀 Starting Argo Search Bot...")

    # Init DB
    db = SearchDatabase()
    logger.info("✅ Database ready")

    # Init Telethon scraper
    scraper = TelegramScraper(db)
    logger.info("🔌 Connecting to Telegram API (Telethon)...")
    await scraper.start()
    logger.info("✅ Telethon connected — real Telegram search enabled!")

    # Init search engine with scraper
    engine = SearchEngine(db, scraper=scraper)

    # Start bot (pass scraper + engine into bot context)
    await bot_main(db=db, engine=engine, scraper=scraper)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════╗
║       🔍 ARGO SEARCH BOT            ║
║   Real Telegram Search Engine       ║
╚══════════════════════════════════════╝
    """)

    # Check env vars first
    check_env()

    # Run
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
