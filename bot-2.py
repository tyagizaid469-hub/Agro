"""
Argo-like Telegram Search Bot
Searches channels, groups, videos, and music on Telegram.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from database import SearchDatabase
from search_engine import SearchEngine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

db     = SearchDatabase()
engine = SearchEngine(db)

# ── Helpers ───────────────────────────────────────────────────────────────────

CATEGORY_ICONS = {
    "channel": "📢",
    "group":   "👥",
    "video":   "🎬",
    "music":   "🎵",
}

def format_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n//1_000}k"
    return str(n)

def build_results_text(results: list, query: str) -> str:
    if not results:
        return f"❌ No results found for *{query}*\n\nTry a different keyword."
    lines = [f"🔍 Results for *{query}* — {len(results)} found\n"]
    for r in results:
        icon  = CATEGORY_ICONS.get(r["type"], "📌")
        count = format_count(r["members"])
        name  = r["name"]
        link  = r.get("link", "")
        if link:
            lines.append(f"{icon} [{name}]({link}) — {count}")
        else:
            lines.append(f"{icon} {name} — {count}")
    return "\n".join(lines)

def build_trending_keyboard(trending: list) -> InlineKeyboardMarkup:
    """5-column grid of trending keywords."""
    buttons, row = [], []
    for i, kw in enumerate(trending[:25], 1):
        row.append(InlineKeyboardButton(kw, callback_data=f"search:{kw}"))
        if i % 5 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def build_filter_keyboard(query: str) -> InlineKeyboardMarkup:
    cats = [("All", "all"), ("Channels", "channel"),
            ("Groups", "group"), ("Videos", "video"), ("Music", "music")]
    row = [InlineKeyboardButton(label, callback_data=f"filter:{query}:{cat}")
           for label, cat in cats]
    return InlineKeyboardMarkup([row])

# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trending = db.get_trending(limit=25)
    text = (
        "🔍 *Argo Search Bot*\n\n"
        "The search engine for Telegram!\n"
        "Find *groups, channels, videos, and music* instantly.\n\n"
        "Just send any keyword to search 👇\n\n"
        "🔥 *Recent Trending Searches*\n"
        "Send a keyword 🔍 to find what interests you"
    )
    kb = build_trending_keyboard(trending)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "• Send any keyword to search\n"
        "• Tap filter buttons to narrow by type\n"
        "• Tap trending buttons for popular topics\n\n"
        "Commands:\n"
        "/start — Home & trending\n"
        "/trending — Show trending searches\n"
        "/help — This message",
        parse_mode="Markdown",
    )

async def trending_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trending = db.get_trending(limit=25)
    kb = build_trending_keyboard(trending)
    await update.message.reply_text(
        "🔥 *Trending Searches*\nTap a keyword to search:",
        parse_mode="Markdown",
        reply_markup=kb,
    )

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    db.log_search(query)
    results = engine.search(query)
    text    = build_results_text(results, query)
    kb      = build_filter_keyboard(query)

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb,
        disable_web_page_preview=True,
    )

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query_obj = update.callback_query
    await query_obj.answer()
    data = query_obj.data

    # ── Trending keyword tapped ───────────────────────────────────────────────
    if data.startswith("search:"):
        kw = data.split(":", 1)[1]
        db.log_search(kw)
        results = engine.search(kw)
        text    = build_results_text(results, kw)
        kb      = build_filter_keyboard(kw)
        await query_obj.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
            disable_web_page_preview=True,
        )

    # ── Category filter tapped ────────────────────────────────────────────────
    elif data.startswith("filter:"):
        _, kw, cat = data.split(":", 2)
        results = engine.search(kw, category=None if cat == "all" else cat)
        text    = build_results_text(results, kw)
        kb      = build_filter_keyboard(kw)
        try:
            await query_obj.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=kb,
                disable_web_page_preview=True,
            )
        except Exception:
            await query_obj.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=kb,
                disable_web_page_preview=True,
            )

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("trending", trending_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
