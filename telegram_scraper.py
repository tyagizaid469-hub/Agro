"""
telegram_scraper.py
Real Telegram search using Telethon (user account API).
Searches actual Telegram — channels, groups, videos, music.
Results cached in SQLite database for fast repeated searches.
"""

import asyncio
import os
import re
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import (
    Channel, Chat,
    InputPeerEmpty,
)
from database import SearchDatabase

# ── Credentials (from environment variables) ──────────────────────────────────
# Get these from https://my.telegram.org
API_ID   = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# ── Type detection keywords ───────────────────────────────────────────────────
VIDEO_KEYWORDS = ["video", "movie", "film", "episode", "series", "cinema",
                  "watch", "stream", "webseries", "ott", "netflix", "prime"]
MUSIC_KEYWORDS = ["music", "song", "audio", "mp3", "playlist", "album",
                  "track", "lofi", "beats", "bhajan", "remix", "gaana"]


def detect_type(name: str, description: str, is_group: bool) -> str:
    text = (name + " " + description).lower()
    if is_group:
        return "group"
    for kw in VIDEO_KEYWORDS:
        if kw in text:
            return "video"
    for kw in MUSIC_KEYWORDS:
        if kw in text:
            return "music"
    return "channel"


def make_tags(name: str, description: str) -> str:
    """Extract keywords from name and description for search tagging."""
    text = re.sub(r"[^\w\s]", " ", (name + " " + description).lower())
    words = [w for w in text.split() if len(w) > 2]
    return ",".join(list(dict.fromkeys(words))[:30])  # unique, max 30


class TelegramScraper:
    def __init__(self, db: SearchDatabase):
        self.db     = db
        self.client = TelegramClient("search_session", API_ID, API_HASH)

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.disconnect()

    async def search_telegram(self, query: str, limit: int = 20) -> list:
        """
        Search real Telegram using Telethon SearchRequest.
        Results are saved to database and returned.
        """
        results = []
        try:
            search_result = await self.client(
                SearchRequest(
                    q=query,
                    limit=limit,
                )
            )

            for chat in search_result.chats:
                try:
                    name        = getattr(chat, "title", "") or ""
                    username    = getattr(chat, "username", "") or ""
                    members     = getattr(chat, "participants_count", 0) or 0
                    is_group    = isinstance(chat, Chat) or getattr(chat, "megagroup", False)
                    description = ""

                    # Try to get description
                    try:
                        if username and isinstance(chat, Channel):
                            full = await self.client(GetFullChannelRequest(chat))
                            description = getattr(full.full_chat, "about", "") or ""
                    except Exception:
                        pass

                    link = f"https://t.me/{username}" if username else ""
                    if not link:
                        continue  # skip private channels with no username

                    entry_type = detect_type(name, description, is_group)
                    tags       = make_tags(name, description)

                    entry = {
                        "name":        name,
                        "description": description,
                        "type":        entry_type,
                        "members":     members,
                        "link":        link,
                        "tags":        tags,
                    }
                    results.append(entry)

                    # Save to database (upsert by link)
                    self.db.upsert_entry(
                        name, description, entry_type, members, link, tags
                    )

                except Exception as e:
                    print(f"Error processing chat: {e}")
                    continue

        except Exception as e:
            print(f"Telegram search error: {e}")

        return sorted(results, key=lambda x: x["members"], reverse=True)
