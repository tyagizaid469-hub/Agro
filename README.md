# 🔍 Argo Search Bot — Setup Guide

A Telegram search bot that finds channels, groups, videos, and music — just like Argo Search.

---

## 📁 Files

```
argo_search_bot/
├── bot.py            ← Main bot (handlers, UI)
├── database.py       ← SQLite database + FTS search
├── search_engine.py  ← Search logic layer
├── requirements.txt  ← Dependencies
└── README.md         ← This file
```

---

## ⚙️ Step 1 — Get a Bot Token

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Give your bot a name (e.g. `My Search Bot`)
4. Give it a username ending in `bot` (e.g. `mysearch_bot`)
5. BotFather gives you a **token** like:
   ```
   123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
   ```

---

## 🐍 Step 2 — Install Python & Dependencies

```bash
# Make sure Python 3.10+ is installed
python --version

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Step 3 — Run the Bot

**Option A — Set token as environment variable (recommended):**
```bash
export BOT_TOKEN="your_token_here"
python bot.py
```

**Option B — Edit bot.py directly:**
Open `bot.py` and replace:
```python
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
```
with:
```python
BOT_TOKEN = "123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ"
```
Then run:
```bash
python bot.py
```

---

## 💬 How to Use the Bot

| Action | Result |
|--------|--------|
| `/start` | Welcome screen + trending keywords |
| `/trending` | Show trending search keywords |
| `/help` | Help message |
| Send any text | Search for channels, groups, videos, music |
| Tap a trending button | Search that keyword |
| Tap All/Channels/Groups/Videos/Music | Filter results by type |

---

## ➕ Adding More Content to the Database

The database comes pre-seeded with 30+ sample entries.

To add your own, use the `add_entry()` method in `database.py`:

```python
from database import SearchDatabase

db = SearchDatabase()
db.add_entry(
    name="My Channel",
    description="A great channel about technology",
    entry_type="channel",   # channel | group | video | music
    members=5000,
    link="https://t.me/mychannel",
    tags="tech,gadgets,india,review"
)
```

Or you can build an admin panel bot command to add entries via Telegram.

---

## 🌐 Deploy 24/7 (Optional)

**Free options:**
- **Railway.app** — push your code, set `BOT_TOKEN` env var, done
- **Render.com** — same idea
- **PythonAnywhere** — free tier supports always-on bots
- **Your own VPS** — run with `nohup python bot.py &`

---

## 📊 Features

- ✅ Full-text search (FTS5) for fast results
- ✅ Fallback LIKE search for partial matches
- ✅ Search channels, groups, videos, and music
- ✅ Filter results by category
- ✅ Trending searches (auto-updated based on usage)
- ✅ Member count displayed for each result
- ✅ Clickable links to Telegram resources
- ✅ SQLite database (zero setup, runs anywhere)

---

## 🔧 Scaling Up

To handle millions of users like Argo (2.7M monthly):
1. Replace SQLite with **PostgreSQL**
2. Add a **Redis** cache for trending queries
3. Use **webhook mode** instead of polling
4. Deploy on a **VPS or cloud server**

The code structure is already separated (database.py, search_engine.py) to make this upgrade easy.
