"""
search_engine.py — Search logic layer.
Wraps the database and adds ranking/fuzzy logic.
"""

from database import SearchDatabase


class SearchEngine:
    def __init__(self, db: SearchDatabase):
        self.db = db

    def search(self, query: str, category: str = None, limit: int = 20) -> list:
        """
        Try FTS first; fall back to LIKE search if no results.
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
