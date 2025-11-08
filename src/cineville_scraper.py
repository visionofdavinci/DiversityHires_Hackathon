"""
Cineville Scraper - Get real movie showtimes from Cineville
Uses Cineville public API for reliable scraping.
"""

import json
import re
from datetime import datetime, timedelta

import pytz
import requests
# from bs4 import BeautifulSoup  # Only needed if you go back to HTML scraping


class CinevilleScraper:
    def __init__(self):
        self.api_url = "https://api.cineville.nl/events/search"
        self.timezone = pytz.timezone("Europe/Amsterdam")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )

        # Known Amsterdam cinemas – used when you want to limit to Amsterdam
        self.amsterdam_cinemas = [
            "eye",
            "rialto",
            "kriterion",
            "ketelhuis",
            "the movies",
            "lab111",
            "uitkijk",
            "studio/k",
            "cinecenter",
            "filmhallen",
            "de balie",
        ]

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def get_showtimes_today(self, limit_amsterdam: bool = True):
        """
        Backwards-compatible helper: get showtimes from *now* until end of today.
        """
        return self.get_all_showtimes(days_ahead=1, limit_amsterdam=limit_amsterdam)

    def get_all_showtimes(self, days_ahead: int = 7, limit_amsterdam: bool = True):
        """
        Get ALL upcoming showtimes for the next `days_ahead` days.

        Returns a flat list of showtime dicts:
        {
            'title': str,
            'cinema': str,
            'showtime': datetime (Europe/Amsterdam),
            'source': 'cineville-api' | 'fallback',
            'duration': int | None,  # minutes
            'year': int | None
        }
        """
        print("\n" + "=" * 60)
        print("CINEVILLE API SCRAPER - ALL SHOWTIMES")
        print("=" * 60)

        try:
            now = datetime.now(self.timezone)

            # Start: now; End: now + days_ahead (exclusive)
            start_dt_local = now
            end_dt_local = now + timedelta(days=days_ahead)

            start_date_utc = start_dt_local.astimezone(pytz.UTC).isoformat()
            end_date_utc = end_dt_local.astimezone(pytz.UTC).isoformat()

            payload = {
                "productionId": {"isNull": False},
                "startDate": {"gte": start_date_utc, "lt": end_date_utc},
                "venue": {},
                "page": {"limit": 300},  # should be plenty; adjust if needed
                "isHidden": {"eq": False},
                "embed": {
                    "production": True,
                    "venue": True,
                },
                "sort": {"startDate": "asc"},
            }

            print(f"Calling Cineville API for next {days_ahead} days...")
            response = self.session.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "_embedded" not in data or "events" not in data["_embedded"]:
                print("No events in API response")
                return self._get_fallback_data()

            events = data["_embedded"]["events"]
            print(f"API returned {len(events)} events")

            showtimes = []

            for event in events:
                try:
                    embedded = event.get("_embedded", {})
                    production = embedded.get("production", {})
                    venue = embedded.get("venue", {})

                    title = production.get("title")
                    cinema_name = venue.get("name", "")

                    if not title or not cinema_name:
                        continue

                    # Optional: limit to Amsterdam cinemas by name
                    if limit_amsterdam:
                        is_amsterdam = any(
                            ams.lower() in cinema_name.lower()
                            for ams in self.amsterdam_cinemas
                        )
                        if not is_amsterdam:
                            continue

                    start_date_str = event.get("startDate")
                    if not start_date_str:
                        continue

                    # Parse ISO datetime -> timezone aware -> Amsterdam local time
                    showtime = datetime.fromisoformat(
                        start_date_str.replace("Z", "+00:00")
                    ).astimezone(self.timezone)

                    showtimes.append(
                        {
                            "title": title,
                            "cinema": cinema_name,
                            "showtime": showtime,
                            "source": "cineville-api",
                            "duration": production.get("attributes", {}).get(
                                "duration"
                            ),
                            "year": production.get("attributes", {}).get("releaseYear"),
                        }
                    )
                except Exception:
                    # Skip broken event entries, but keep going
                    continue

            print(f"Found {len(showtimes)} showtimes after filtering")

            if not showtimes:
                print("No showtimes found, using fallback mock data")
                return self._get_fallback_data()

            return showtimes

        except Exception as e:
            print(f"API Error: {e}")
            return self._get_fallback_data()

    def get_movies_with_schedule(
        self, days_ahead: int = 7, limit_amsterdam: bool = True
    ):
        """
        Return movies aggregated with all their showtimes.

        Structure:
        [
          {
            'title': str,
            'year': int | None,
            'duration': int | None,
            'source': 'cineville-api' | 'fallback',
            'schedules': {
                'Cinema Name 1': [datetime, datetime, ...],
                'Cinema Name 2': [datetime, ...],
            }
          },
          ...
        ]

        This is what you want to feed into the Letterboxd matcher.
        """
        showtimes = self.get_all_showtimes(
            days_ahead=days_ahead, limit_amsterdam=limit_amsterdam
        )

        movies_by_key = {}

        for show in showtimes:
            title = show["title"]
            year = show.get("year")
            cinema = show["cinema"]
            showtime = show["showtime"]

            key = (self._normalize_title(title), year)

            if key not in movies_by_key:
                movies_by_key[key] = {
                    "title": title,
                    "year": year,
                    "duration": show.get("duration"),
                    "source": show.get("source"),
                    "schedules": {},
                }

            movie_obj = movies_by_key[key]
            movie_obj["schedules"].setdefault(cinema, []).append(showtime)

        # Sort showtimes per cinema for nicer downstream usage
        for movie in movies_by_key.values():
            for cinema, times in movie["schedules"].items():
                movie["schedules"][cinema] = sorted(times)

        movies = list(movies_by_key.values())
        print(f"Aggregated into {len(movies)} unique movies")
        return movies

    # ------------------------------------------------------------------
    # EXISTING HELPERS (still usable if you want)
    # ------------------------------------------------------------------
    def filter_evening_showtimes(
        self, showtimes, start_hour: int = 18, end_hour: int = 23
    ):
        """Filter a flat showtime list for evening showtimes."""
        evening = []

        for show in showtimes:
            if show["showtime"] and isinstance(show["showtime"], datetime):
                hour = show["showtime"].hour
                if start_hour <= hour < end_hour:
                    evening.append(show)

        return evening

    def get_movies_for_free_slot(self, free_start, free_end):
        """
        Old helper: Get movies that fit in a free time slot, based on *today*.
        You probably won't need this right now, but it's kept for later.
        """
        all_showtimes = self.get_showtimes_today()

        matching = []
        for show in all_showtimes:
            if show["showtime"]:
                duration_mins = show.get("duration") or 150  # default 2.5h
                movie_end = show["showtime"] + timedelta(
                    minutes=duration_mins + 30
                )  # + buffer

                if free_start <= show["showtime"] <= free_end:
                    if movie_end <= free_end + timedelta(minutes=30):
                        matching.append(show)

        print(f"\nFound {len(matching)} movies in free slot")
        return matching

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------
    def _normalize_title(self, title: str) -> str:
        """Normalize a movie title for grouping/matching."""
        if not title:
            return ""
        return re.sub(r"[^a-z0-9]+", "", title.lower())

    def _get_fallback_data(self):
        """Fallback mock data if API fails."""
        print("Using fallback mock data")

        now = datetime.now(self.timezone)
        base_time = now.replace(hour=19, minute=0, second=0, microsecond=0)

        return [
            {
                "title": "Perfect Days",
                "cinema": "EYE Filmmuseum",
                "showtime": base_time.replace(hour=19, minute=30),
                "source": "fallback",
                "duration": 123,
                "year": 2023,
            },
            {
                "title": "The Zone of Interest",
                "cinema": "Rialto",
                "showtime": base_time.replace(hour=20, minute=15),
                "source": "fallback",
                "duration": 105,
                "year": 2023,
            },
            {
                "title": "Past Lives",
                "cinema": "Kriterion",
                "showtime": base_time.replace(hour=20, minute=45),
                "source": "fallback",
                "duration": 105,
                "year": 2023,
            },
            {
                "title": "Poor Things",
                "cinema": "LAB111",
                "showtime": base_time.replace(hour=21, minute=30),
                "source": "fallback",
                "duration": 141,
                "year": 2023,
            },
        ]


def test_cineville_scraper():
    """Quick manual test for the Cineville scraper."""
    scraper = CinevilleScraper()

    print("\n" + "=" * 60)
    print("TESTING CINEVILLE API SCRAPER")
    print("=" * 60)

    # 1) Flat showtimes for the next 3 days
    print("\nTest 1: Getting flat showtimes for next 3 days...")
    showtimes = scraper.get_all_showtimes(days_ahead=3)

    if showtimes:
        print(f"\nFound {len(showtimes)} showtimes (first 10):")
        for i, show in enumerate(showtimes[:10], 1):
            time_str = show["showtime"].strftime("%Y-%m-%d %H:%M")
            duration = (
                f" ({show.get('duration', '?')} min)" if show.get("duration") else ""
            )
            print(f"  {i:2d}. {time_str} - {show['title']}{duration}")
            print(f"       {show['cinema']} [{show['source']}]")

    # 2) Aggregated movies with schedule
    print("\nTest 2: Aggregated movies with schedule (next 3 days)...")
    movies = scraper.get_movies_with_schedule(days_ahead=3)

    print(f"\nFound {len(movies)} unique movies (first 5):")
    for movie in movies[:5]:
        print(f"• {movie['title']} ({movie.get('year', '?')})")
        for cinema, times in movie["schedules"].items():
            times_str = ", ".join(t.strftime("%d/%m %H:%M") for t in times[:3])
            extra = "..." if len(times) > 3 else ""
            print(f"   - {cinema}: {times_str}{extra}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)

    return scraper


if __name__ == "__main__":
    test_cineville_scraper()

"""
How you’ll use this for Letterboxd matching
From your orchestrator / movie matcher you can now do:

python
Copy code
from cineville_scraper import CinevilleScraper

scraper = CinevilleScraper()
movies = scraper.get_movies_with_schedule(days_ahead=7)
"""

# Example movie object
# {
#   'title': 'Poor Things',
#   'year': 2023,
#   'duration': 141,
#   'source': 'cineville-api',
#   'schedules': {
#       'LAB111': [datetime(...), datetime(...), ...],
#       'EYE Filmmuseum': [...],
#   }
# }

# Then pass `title` (and `year` if needed) into your Letterboxd integration.