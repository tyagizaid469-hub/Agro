"""
Argo-like Telegram Search Bot — REAL SEARCH VERSION
- Searches REAL Telegram channels/groups/videos/music via Telethon
- Results cached in SQLite for instant repeat searches
- Clickable URL buttons for every result
- Filter by type: Channels / Groups / Videos / Music
"""

import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Injected by run.py before main() is called
db      = None
engine  = None
scraper = None

# ── Icons ─────────────────────────────────────────────────────────────────────
TYPE_ICON = {
    "channel": "📢",
    "group":   "👥",
    "video":   "🎬",
    "music":   "🎵",
}
TYPE_LABEL = {
    "channel": "Channel",
    "group":   "Group",
    "video":   "Video",
    "music":   "Music",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def format_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


def build_results_message(results: list, query: str, category: str = "all"):
    if not results:
        text = (
            f"❌ *No results for* `{query}`\n\n"
            "Try a different keyword or broaden your search."
        )
        return text, None

    cat_label = "" if category == "all" else f" › {category.title()}"
    text = f"🔍 *Results for* `{query}`{cat_label} — *{len(results)} found*\n\n"

    buttons = []
    for r in results:
        icon  = TYPE_ICON.get(r["type"], "📌")
        label = TYPE_LABEL.get(r["type"], "")
        count = format_count(r["members"])
        name  = r["name"]
        link  = r.get("link", "").strip()
        desc  = r.get("description", "")

        text += f"{icon} *{name}*\n"
        if desc:
            short_desc = desc[:80] + "..." if len(desc) > 80 else desc
            text += f"    _{short_desc}_\n"
        text += f"    👥 {count}  •  {label}\n\n"

        if link:
            buttons.append([
                InlineKeyboardButton(f"{icon} Open: {name} ({count})", url=link)
            ])

    filter_row = [
        InlineKeyboardButton("🔄 All",      callback_data=f"filter:{query}:all"),
        InlineKeyboardButton("📢 Channels", callback_data=f"filter:{query}:channel"),
        InlineKeyboardButton("👥 Groups",   callback_data=f"filter:{query}:group"),
        InlineKeyboardButton("🎬 Videos",   callback_data=f"filter:{query}:video"),
        InlineKeyboardButton("🎵 Music",    callback_data=f"filter:{query}:music"),
    ]
    buttons.append(filter_row)
    return text, InlineKeyboardMarkup(buttons)


def build_trending_keyboard(trending: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for i, kw in enumerate(trending[:25], 1):
        row.append(InlineKeyboardButton(kw, callback_data=f"search:{kw}"))
        if i % 5 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trending = db.get_trending(limit=25)
    text = (
        "🔍 *Argo Search Bot*\n\n"
        "Search for *real* channels, groups, videos & music on Telegram!\n\n"
        "Just type any keyword below 👇\n\n"
        "🔥 *Trending Searches* — tap to search instantly:"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_trending_keyboard(trending),
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "• Type any keyword to search real Telegram\n"
        "• Tap a result button to open it directly\n"
        "• Use filter buttons to narrow by type\n"
        "• Results are cached — repeat searches are instant\n\n"
        "Commands:\n"
        "/start — Home & trending\n"
        "/trending — Show trending searches\n"
        "/help — This message",
        parse_mode="Markdown",
    )


async def trending_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trending = db.get_trending(limit=25)
    await update.message.reply_text(
        "🔥 *Trending Searches*\nTap a keyword to search instantly:",
        parse_mode="Markdown",
        reply_markup=build_trending_keyboard(trending),
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    db.log_search(query)

    loading_msg = await update.message.reply_text(
        f"🔍 Searching Telegram for *{query}*...",
        parse_mode="Markdown",
    )

    try:
        results = await engine.async_search(query)
        text, kb = build_results_message(results, query)
        await loading_msg.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        await loading_msg.edit_text(
            "⚠️ Search failed. Please try again.",
            parse_mode="Markdown",
        )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("search:"):
        kw = data.split(":", 1)[1]
        db.log_search(kw)

        await q.message.reply_text(
            f"🔍 Searching Telegram for *{kw}*...",
            parse_mode="Markdown",
        )

        results = await engine.async_search(kw)
        text, kb = build_results_message(results, kw)
        await q.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
            disable_web_page_preview=True,
        )

    elif data.startswith("filter:"):
        parts = data.split(":", 2)
        kw  = parts[1]
        cat = parts[2]
        results = db.search(kw, category=None if cat == "all" else cat)
        text, kb = build_results_message(results, kw, category=cat)
        try:
            await q.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=kb,
                disable_web_page_preview=True,
            )
        except Exception:
            await q.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=kb,
                disable_web_page_preview=True,
            )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    """
    Bot ka main loop — existing event loop ke andar run karta hai.
    run_polling() ki jagah manual initialize/start/idle use karo
    taaki Telethon ke asyncio.run() loop se conflict na ho.
    """
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("trending", trending_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("✅ Bot is running!")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Run forever until cancelled
        await asyncio.Event().wait()

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    async def _self_run():
        global db, engine, scraper
        from database import SearchDatabase
        from search_engine import SearchEngine
        from telegram_scraper import TelegramScraper
        db      = SearchDatabase()
        scraper = TelegramScraper(db)
        engine  = SearchEngine(db, scraper=scraper)
        logger.info("🔌 Connecting to Telegram API...")
        await scraper.start()
        logger.info("✅ Telethon connected!")
        await main()
    asyncio.run(_self_run())
