"""
Argo-like Telegram Search Bot — FIXED VERSION
- Every result has its own clickable URL button (opens Telegram directly)
- Strong search: FTS5 + LIKE fallback + partial word match
- Filter buttons work properly
- No more "Username not found" error
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

db     = SearchDatabase()
engine = SearchEngine(db)

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
    """
    Returns (text, reply_markup).
    Each result gets its own URL button so the user can tap to open directly.
    """
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
        icon    = TYPE_ICON.get(r["type"], "📌")
        label   = TYPE_LABEL.get(r["type"], "")
        count   = format_count(r["members"])
        name    = r["name"]
        link    = r.get("link", "").strip()
        desc    = r.get("description", "")

        # Text line in message
        text += f"{icon} *{name}*\n"
        if desc:
            text += f"    _{desc}_\n"
        text += f"    👥 {count}  •  {label}\n\n"

        # Inline URL button — opens Telegram channel/group directly
        if link:
            buttons.append([InlineKeyboardButton(f"{icon} {name} ({count})", url=link)])

    # Filter row at the bottom
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
        "Search for *channels, groups, videos & music* on Telegram!\n\n"
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
        "• Type any keyword to search\n"
        "• Tap a result button to open it in Telegram\n"
        "• Use filter buttons to narrow by type\n"
        "• Tap trending keywords for popular topics\n\n"
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
    results = engine.search(query)
    text, kb = build_results_message(results, query)

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb,
        disable_web_page_preview=True,
    )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # ── Trending keyword tapped ───────────────────────────────────────────────
    if data.startswith("search:"):
        kw = data.split(":", 1)[1]
        db.log_search(kw)
        results = engine.search(kw)
        text, kb = build_results_message(results, kw)
        await q.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
            disable_web_page_preview=True,
        )

    # ── Filter button tapped ──────────────────────────────────────────────────
    elif data.startswith("filter:"):
        parts = data.split(":", 2)
        kw  = parts[1]
        cat = parts[2]
        results = engine.search(kw, category=None if cat == "all" else cat)
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

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("trending", trending_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("✅ Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
