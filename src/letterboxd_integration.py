"""
Letterboxd integration (RSS + optional JSON fallback).

Primary source:
    - Public RSS feed: https://letterboxd.com/<username>/rss/

Fallback:
    - data/mock_letterboxd.json (for testing / offline use)

Usage from other modules:
    from letterboxd_integration import LetterboxdIntegration

    lb = LetterboxdIntegration(username="your_username")
    prefs = lb.get_preferences()
    index = lb.build_index()

You can run this file directly to debug:
    python -m src.letterboxd_integration --username YOUR_NAME
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser  # pip install feedparser


# ----------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------
@dataclass
class MoviePreference:
    """User preference for a single movie."""

    title: str
    year: Optional[int] = None
    rating: Optional[float] = None  # 0.5–5.0 (Letterboxd stars)
    liked: bool = False
    rewatch: bool = False
    watched_date: Optional[datetime] = None
    source: str = "letterboxd-rss"  # or "manual", "letterboxd-api"


# ----------------------------------------------------------------------
# Main integration class
# ----------------------------------------------------------------------
class LetterboxdIntegration:
    """
    High-level entry point for getting Letterboxd preferences.

    Sources:
        1) RSS feed for the given username
        2) Local JSON fallback (data/mock_letterboxd.json)
    """

    def __init__(
        self,
        username: Optional[str] = None,
        max_items: int = 200,
        data_dir: Optional[Path] = None,
    ) -> None:
        """
        :param username: Letterboxd username (for RSS). If None, only JSON fallback is used.
        :param max_items: Max RSS items to read (feed is usually ~50 anyway).
        :param data_dir: Where to look for mock_letterboxd.json.
                         Defaults to "<project_root>/data".
        """
        self.username = username
        self.max_items = max_items

        if data_dir is None:
            # src/letterboxd_integration.py -> project root -> data/
            self.data_dir = Path(__file__).resolve().parents[1] / "data"
        else:
            self.data_dir = Path(data_dir)

    # ------------------------------------------------------------------
    # Public API used by the rest of the project
    # ------------------------------------------------------------------
    def get_preferences(
        self,
        include_rss: bool = True,
        include_manual: bool = True,
        manual_filename: str = "mock_letterboxd.json",
    ) -> List[MoviePreference]:
        """
        Return a list of MoviePreference.

        - If include_rss and username is set: use RSS feed.
        - If include_manual: also load a JSON file and merge.
        """
        merged: Dict[Tuple[str, Optional[int]], MoviePreference] = {}

        # 1) RSS
        if include_rss:
            if self.username:
                rss_prefs = self._fetch_from_rss()
                for p in rss_prefs:
                    key = (self._normalize_title(p.title), p.year)
                    merged[key] = p
            else:
                print("[Letterboxd] No username provided, skipping RSS.")

        # 2) Manual JSON fallback
        if include_manual:
            manual_path = self.data_dir / manual_filename
            manual_prefs = self._load_manual_preferences(manual_path)
            for p in manual_prefs:
                key = (self._normalize_title(p.title), p.year)
                # Do not overwrite RSS data if it exists
                merged.setdefault(key, p)

        if not merged:
            print(
                "[Letterboxd] WARNING: no preferences found.\n"
                "  -> Either set LETTERBOXD_USERNAME / pass --username\n"
                "  -> Or fill data/mock_letterboxd.json with sample data."
            )

        # Return unique MoviePreference objects
        return list(merged.values())

    def build_index(
        self,
        include_rss: bool = True,
        include_manual: bool = True,
        manual_filename: str = "mock_letterboxd.json",
    ) -> Dict[Tuple[str, Optional[int]], MoviePreference]:
        """
        Build index: (normalized_title, year) -> MoviePreference

        Also stores a (normalized_title, None) entry as a year-agnostic fallback.
        """
        prefs = self.get_preferences(
            include_rss=include_rss,
            include_manual=include_manual,
            manual_filename=manual_filename,
        )

        index: Dict[Tuple[str, Optional[int]], MoviePreference] = {}

        for p in prefs:
            norm = self._normalize_title(p.title)
            key_with_year = (norm, p.year)
            index[key_with_year] = p

            if p.year is not None:
                key_without_year = (norm, None)
                # Use the first one that appears for the year-less fallback
                index.setdefault(key_without_year, p)

        return index

    # ------------------------------------------------------------------
    # RSS backend
    # ------------------------------------------------------------------
    def _fetch_from_rss(self) -> List[MoviePreference]:
        """Fetch recent activity from the public RSS feed."""
        if not self.username:
            return []

        url = f"https://letterboxd.com/{self.username}/rss/"
        print(f"[Letterboxd] Fetching RSS feed for '{self.username}'...")
        feed = feedparser.parse(url)

        if feed.bozo:
            # 'bozo' means parsing error (invalid feed, network issue, etc.)
            print(f"[Letterboxd] RSS parse error: {feed.bozo_exception}")
            return []

        entries = feed.entries[: self.max_items] if self.max_items else feed.entries

        prefs: List[MoviePreference] = []
        for entry in entries:
            pref = self._rss_entry_to_pref(entry)
            if pref is not None:
                prefs.append(pref)

        print(f"[Letterboxd] RSS returned {len(prefs)} entries.")
        return prefs

    def _rss_entry_to_pref(self, entry) -> Optional[MoviePreference]:
        """
        Convert one RSS entry into a MoviePreference.

        Letterboxd RSS exposes custom fields like:
          - entry.letterboxd_filmtitle
          - entry.letterboxd_filmyear
          - entry.letterboxd_memberrating
        """
        # Title
        title = getattr(entry, "letterboxd_filmtitle", None)
        year = getattr(entry, "letterboxd_filmyear", None)

        # Fallback: parse from generic title text
        if not title:
            raw_title = getattr(entry, "title", "") or ""
            title, inferred_year = self._parse_title_and_year_from_string(raw_title)
            if year is None and inferred_year is not None:
                year = inferred_year

        if not title:
            # Probably not a film entry
            return None

        # Year normalization
        year_int: Optional[int] = None
        if isinstance(year, str) and year.isdigit():
            year_int = int(year)
        elif isinstance(year, int):
            year_int = year

        # Rating
        rating_raw = getattr(entry, "letterboxd_memberrating", None)
        rating_val: Optional[float] = None
        if isinstance(rating_raw, str):
            try:
                rating_val = float(rating_raw)
            except ValueError:
                rating_val = None

        # Liked / rewatch heuristics
        summary = getattr(entry, "summary", "") or ""
        title_str = getattr(entry, "title", "") or ""
        liked = "Liked" in summary or "Liked" in title_str
        rewatch = "rewatched" in summary.lower() or "rewatch" in summary.lower()

        # Watched date (approximate: use published date)
        watched_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            watched_date = datetime(*entry.published_parsed[:6])

        return MoviePreference(
            title=title,
            year=year_int,
            rating=rating_val,
            liked=liked,
            rewatch=rewatch,
            watched_date=watched_date,
            source="letterboxd-rss",
        )

    def _parse_title_and_year_from_string(
        self, text: str
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Try to extract title + year from strings like:
          "teodora watched Poor Things (2023)"
        """
        m = re.search(r"(.+?)\s*\((\d{4})\)\s*$", text)
        if not m:
            return None, None

        before_year = m.group(1)
        year = int(m.group(2))

        # Strip "username watched/reviewed/rated" prefix
        cleaned = re.sub(
            r"^\s*\S+\s+(watched|reviewed|rated|liked|logged)\s+",
            "",
            before_year,
            flags=re.IGNORECASE,
        ).strip()

        if not cleaned:
            return None, None

        return cleaned, year

    # ------------------------------------------------------------------
    # Manual JSON backend
    # ------------------------------------------------------------------
    def _load_manual_preferences(self, path: Path) -> List[MoviePreference]:
        """
        Load preferences from a JSON file.

        Default path:
            <project_root>/data/mock_letterboxd.json

        Example JSON:

        [
          { "title": "Poor Things", "year": 2023, "rating": 4.5, "liked": true },
          { "title": "Past Lives", "year": 2023, "rating": 5.0 }
        ]
        """
        if not path.exists():
            print(f"[Letterboxd] Manual JSON not found at {path}")
            return []

        text = path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"[Letterboxd] Manual JSON file is empty: {path}")
            return []

        try:
            raw = json.loads(text)
        except Exception as e:
            print(f"[Letterboxd] Error reading manual JSON: {e}")
            return []

        prefs: List[MoviePreference] = []

        if isinstance(raw, dict):
            items = raw.values()
        else:
            items = raw

        for item in items:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            if not title:
                continue

            year = item.get("year")
            if isinstance(year, str) and year.isdigit():
                year = int(year)
            elif not isinstance(year, int):
                year = None

            rating = item.get("rating")
            if isinstance(rating, str):
                try:
                    rating = float(rating)
                except Exception:
                    rating = None

            liked = bool(item.get("liked", False))
            rewatch = bool(item.get("rewatch", False))

            prefs.append(
                MoviePreference(
                    title=title,
                    year=year,
                    rating=rating,
                    liked=liked,
                    rewatch=rewatch,
                    watched_date=None,
                    source="manual",
                )
            )

        return prefs

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _normalize_title(self, title: str) -> str:
        if not title:
            return ""
        return re.sub(r"[^a-z0-9]+", "", title.lower())


# ----------------------------------------------------------------------
# CLI / direct run for debugging
# ----------------------------------------------------------------------
def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Test LetterboxdIntegration (RSS + JSON)."
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Letterboxd username (or set LETTERBOXD_USERNAME env var)",
    )
    parser.add_argument(
        "--no-rss",
        action="store_true",
        help="Disable RSS (only use JSON)",
    )
    parser.add_argument(
        "--no-manual",
        action="store_true",
        help="Disable JSON fallback (only use RSS)",
    )

    args = parser.parse_args()

    username = args.username or os.getenv("LETTERBOXD_USERNAME")
    lb = LetterboxdIntegration(username=username)

    prefs = lb.get_preferences(
        include_rss=not args.no_rss,
        include_manual=not args.no_manual,
    )

    print("\nFirst 10 preferences:")
    for p in prefs[:10]:
        print(
            f"• {p.title} ({p.year or '?'}) "
            f"rating={p.rating or '-'} liked={p.liked} src={p.source}"
        )


if __name__ == "__main__":
    _main()