"""
database.py — SQLite storage for the search bot.

Tables:
  entries   — the searchable content (channels, groups, videos, music)
  searches  — search query log (for trending)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "search_bot.db")


class SearchDatabase:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()
        self._seed_sample_data()

    # ── Connection ─────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Init ───────────────────────────────────────────────────────────────────

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS entries (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    type        TEXT NOT NULL,   -- channel | group | video | music
                    members     INTEGER DEFAULT 0,
                    link        TEXT DEFAULT '',
                    tags        TEXT DEFAULT '',  -- comma-separated keywords
                    created_at  TEXT DEFAULT (datetime('now'))
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts
                USING fts5(name, description, tags, content=entries, content_rowid=id);

                CREATE TABLE IF NOT EXISTS searches (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    query      TEXT NOT NULL,
                    searched_at TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(type);
                CREATE INDEX IF NOT EXISTS idx_entries_members ON entries(members DESC);
            """)

    # ── Seed sample data ───────────────────────────────────────────────────────

    def _seed_sample_data(self):
        with self._conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            if count > 0:
                return  # already seeded

            samples = [
                # Channels
                ("The Indian Express",          "Latest news from India",            "channel", 123000, "https://t.me/indianexpress",      "indian,news,express,media"),
                ("Film Companion",              "Movies reviews and analysis",        "channel", 138000, "https://t.me/filmcompanion",       "film,movie,bollywood,review"),
                ("Crypto Daily",                "Crypto news and market updates",     "channel",  95000, "https://t.me/cryptodailyofficial", "crypto,bitcoin,ethereum,market"),
                ("Stock Market News",           "NSE BSE stock market updates",       "channel",   2000, "https://t.me/stockmarketnews",     "stock,market,nse,bse,trading"),
                ("Live Law",                    "Legal news and judgments",           "channel",  39000, "https://t.me/livelaw",             "law,legal,court,india"),
                ("UPSC History",                "History for UPSC preparation",       "channel",  53000, "https://t.me/upschistory",         "upsc,history,exam,india"),
                ("Anime World",                 "Anime updates and recommendations",  "channel",  75000, "https://t.me/animeworldofficial",  "anime,naruto,onepiece,manga"),
                ("Tech Updates India",          "Latest tech news in India",          "channel",  41000, "https://t.me/techupdatesindia",    "tech,technology,gadgets,india"),
                ("Bollywood Music Hub",         "Latest Bollywood songs",             "channel",  88000, "https://t.me/bollywoodmusichub",   "music,bollywood,hindi,songs"),
                ("Tamil Cinema News",           "Tamil movies and entertainment",     "channel",  62000, "https://t.me/tamilcinemanews",     "tamil,movie,kollywood,cinema"),

                # Groups
                ("Indian Students Group",       "Community for Indian students",      "group",   47000, "https://t.me/indianstudents",      "indian,students,education,group"),
                ("Crypto Traders India",        "Crypto trading discussion India",    "group",  109000, "https://t.me/cryptotradersindia",  "crypto,trading,india,bitcoin"),
                ("Python Developers",           "Python programming community",       "group",   34000, "https://t.me/pythondevs",          "python,programming,developer,code"),
                ("UPSC Economy MCQ",            "Economy MCQs for UPSC",             "group",   47000, "https://t.me/upsceconomymcq",      "upsc,economy,mcq,exam"),
                ("Movie Lovers India",          "Discuss movies in India",            "group",   28000, "https://t.me/movielovers",         "movie,film,bollywood,india"),
                ("Anime Fans India",            "Anime fans community India",         "group",   19000, "https://t.me/animefansindia",      "anime,naruto,onepiece,india"),
                ("Tamil Learning Group",        "Learn Tamil language",               "group",   12000, "https://t.me/tamillearn",          "tamil,language,learning"),
                ("Stock Traders Group",         "NSE BSE trading tips",               "group",   55000, "https://t.me/stocktraders",        "stock,trading,nse,bse,market"),

                # Videos
                ("Naruto Full Episodes",        "All Naruto episodes in Hindi",       "video",   21000, "https://t.me/narutoepisodeshindi", "naruto,anime,hindi,episodes,video"),
                ("Bollywood Movies HD",         "Latest Bollywood movies",            "video",   66000, "https://t.me/bollywoodmovies",     "bollywood,movie,hindi,video,film"),
                ("One Piece Episodes",          "One Piece anime episodes",           "video",   31000, "https://t.me/onepieceepisodes",    "onepiece,anime,video,episodes"),
                ("Tamil Movies 2024",           "Tamil dubbed and original movies",   "video",   48000, "https://t.me/tamilmovies2024",     "tamil,movie,video,cinema"),
                ("Desi Videos Hub",             "Viral desi videos",                  "video",   14000, "https://t.me/desivideos",          "desi,indian,viral,video"),
                ("Classroom Study Videos",      "Educational study videos",           "video",   27000, "https://t.me/classroomstudy",      "classroom,study,education,video"),
                ("Jujutsu Kaisen HD",           "Jujutsu Kaisen episodes",            "video",   18000, "https://t.me/jujutsukaisenhd",     "jujutsu,kaisen,anime,video"),
                ("Stranger Things Clips",       "Best clips from Stranger Things",    "video",    9000, "https://t.me/strangerthingsclips", "stranger,things,netflix,video"),

                # Music
                ("Hindi Songs 2024",            "Latest Hindi songs collection",      "music",   82000, "https://t.me/hindisongs2024",      "hindi,songs,music,bollywood"),
                ("Tamil Songs Hub",             "Tamil music collection",             "music",   44000, "https://t.me/tamilsongshub",       "tamil,songs,music,kollywood"),
                ("Yoasobi Music",               "Yoasobi Japanese music",             "music",   13000, "https://t.me/yoasobi",             "yoasobi,japanese,anime,music"),
                ("Desi Music Club",             "Desi and Punjabi music",             "music",   36000, "https://t.me/desimusicclub",       "desi,punjabi,music,bhangra"),
                ("Lofi Study Music",            "Lo-fi music for studying",           "music",   25000, "https://t.me/lofistudy",           "lofi,study,music,chill"),
                ("Bollywood Retro Songs",       "Old Bollywood classic songs",        "music",   19000, "https://t.me/bollywoodretro",      "bollywood,retro,classic,music"),
            ]

            conn.executemany(
                "INSERT INTO entries (name, description, type, members, link, tags) VALUES (?,?,?,?,?,?)",
                samples,
            )

            # Rebuild FTS index
            conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(self, query: str, category: str = None, limit: int = 20) -> list:
        """Full-text search with optional category filter."""
        sql_params = [query]
        cat_filter = ""
        if category:
            cat_filter = "AND e.type = ?"
            sql_params.append(category)

        sql = f"""
            SELECT e.id, e.name, e.description, e.type, e.members, e.link
            FROM entries_fts
            JOIN entries e ON entries_fts.rowid = e.id
            WHERE entries_fts MATCH ?
            {cat_filter}
            ORDER BY e.members DESC
            LIMIT ?
        """
        sql_params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(sql, sql_params).fetchall()
            return [dict(r) for r in rows]

    def search_fallback(self, query: str, category: str = None, limit: int = 20) -> list:
        """LIKE-based fallback when FTS returns nothing."""
        like = f"%{query}%"
        params = [like, like, like]
        cat_filter = ""
        if category:
            cat_filter = "AND type = ?"
            params.append(category)
        params.append(limit)

        sql = f"""
            SELECT id, name, description, type, members, link
            FROM entries
            WHERE (name LIKE ? OR description LIKE ? OR tags LIKE ?)
            {cat_filter}
            ORDER BY members DESC
            LIMIT ?
        """
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    # ── Trending ───────────────────────────────────────────────────────────────

    def log_search(self, query: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO searches (query) VALUES (?)", (query.lower().strip(),)
            )

    def get_trending(self, limit: int = 25) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT query, COUNT(*) as cnt
                FROM searches
                WHERE searched_at >= datetime('now', '-7 days')
                GROUP BY query
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            keywords = [r["query"] for r in rows]

            # Pad with default trending if not enough data
            defaults = [
                "Indian", "Crypto", "Anime", "Hindi", "Tamil",
                "Movies", "Music", "UPSC", "Stock", "Naruto",
                "Bollywood", "One piece", "Video", "Adult", "Viral",
                "18+", "Classroom", "Movie", "Ullu", "Desi",
                "Mallu", "Gay", "Hot", "Tamil", "Trans",
            ]
            for d in defaults:
                if d.lower() not in keywords and len(keywords) < limit:
                    keywords.append(d)

            return keywords[:limit]

    # ── Admin helpers ──────────────────────────────────────────────────────────

    def add_entry(self, name: str, description: str, entry_type: str,
                  members: int, link: str, tags: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO entries (name, description, type, members, link, tags) VALUES (?,?,?,?,?,?)",
                (name, description, entry_type, members, link, tags),
            )
            entry_id = cur.lastrowid
            conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
            return entry_id

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total    = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            channels = conn.execute("SELECT COUNT(*) FROM entries WHERE type='channel'").fetchone()[0]
            groups   = conn.execute("SELECT COUNT(*) FROM entries WHERE type='group'").fetchone()[0]
            videos   = conn.execute("SELECT COUNT(*) FROM entries WHERE type='video'").fetchone()[0]
            music    = conn.execute("SELECT COUNT(*) FROM entries WHERE type='music'").fetchone()[0]
            searches = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
            return {
                "total": total, "channels": channels, "groups": groups,
                "videos": videos, "music": music, "total_searches": searches,
            }
