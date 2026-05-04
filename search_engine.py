"""
search_engine.py — Search logic layer.
Wraps the database and adds ranking/fuzzy logic.
Real-time Telegram search via TelegramScraper.
"""

from database import SearchDatabase


class SearchEngine:
    def __init__(self, db: SearchDatabase, scraper=None):
        self.db = db
        self.scraper = scraper  # TelegramScraper instance (optional)

    def search(self, query: str, category: str = None, limit: int = 20) -> list:
        """
        Try FTS first; fall back to LIKE search if no results.
        Sync version — used for filter callbacks (DB only).
        """
        query = query.strip()
        if not query:
            return []

        # FTS search
        try:
            results = self.db.search(query, category=category, limit=limit)
        except Exception:
            results = []

        # Fallback to LIKE search
        if not results:
            results = self.db.search_fallback(query, category=category, limit=limit)

        return results

    async def async_search(self, query: str, category: str = None, limit: int = 20) -> list:
        """
        Async search: pehle real Telegram scrape karo (agar scraper available hai),
        phir DB se results return karo.
        """
        query = query.strip()
        if not query:
            return []

        # Step 1: Real Telegram se fresh results fetch karo
        if self.scraper is not None:
            try:
                await self.scraper.scrape_query(query)
            except Exception:
                pass  # Scrape fail ho toh DB fallback use hoga

        # Step 2: DB se return karo (ab fresh data bhi hai)
        return self.search(query, category=category, limit=limit)
