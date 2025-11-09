"""
movie_matcher.py

Group movie matching with learned personal profiles + calendar availability.

- For each user:
    - Pull ratings from Letterboxd (via LetterboxdIntegration)
    - Pull metadata for rated movies from TMDb
    - Train a RandomForestRegressor to predict preference for new movies

- For a group of users:
    - Get Cineville movies (title + year + schedules)
    - Filter showtimes to **only those that fit in common free calendar slots**
    - For each remaining movie:
        - get TMDb metadata
        - predict a preference score per user
        - combine into a group score
    - Return ranked group recommendations including:
        - title, year
        - per-user scores
        - group score
        - showtimes (cinema + datetime) that fit in free slots
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

TMDB_API_KEY = "0ad625d2ef7503df5817998ca55e0bdf"

# -----------------------------------------------------------------------------
# Robust imports for local modules (cineville_scraper + letterboxd + calendar)
# -----------------------------------------------------------------------------
try:
    # When run as a module: python -m src.movie_matcher
    from .cineville_scraper import CinevilleScraper
    from .letterboxd_integration import LetterboxdIntegration, MoviePreference
    from .calendar_matcher import find_common_available_times
    from .group_history import GroupHistory, create_group_id, GENRE_MAP
    from .mood_filter import MoodFilter
except ImportError:
    # When run as a script: python src/movie_matcher.py
    import sys

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(CURRENT_DIR)
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)

    from cineville_scraper import CinevilleScraper
    from letterboxd_integration import LetterboxdIntegration, MoviePreference
    from calendar_matcher import find_common_available_times
    from group_history import GroupHistory, create_group_id, GENRE_MAP
    from mood_filter import MoodFilter


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def normalize_title_global(title: str) -> str:
    if not title:
        return ""
    return re.sub(r"[^a-z0-9]+", "", title.lower())


# -----------------------------------------------------------------------------
# TMDb Client
# -----------------------------------------------------------------------------
class TMDbClient:
    """
    Minimal TMDb client for searching movies by title (+ optional year).

    Uses TMDB_API_KEY constant by default.
    """

    def __init__(self, api_key=TMDB_API_KEY, language: str = "en-US") -> None:
        self.api_key = api_key or os.getenv("TMDB_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "TMDb API key missing. "
                "Set TMDB_API_KEY in your environment or pass api_key=..."
            )

        self.language = language
        self.base_url = "https://api.themoviedb.org/3"

        self.session = requests.Session()
        self.session.params = {
            "api_key": self.api_key,
            "language": self.language,
        }

    def search_movie(
        self,
        title: str,
        year: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Search TMDb for the given title and (optionally) year.
        Returns the first result, or None if nothing is found.
        """
        url = f"{self.base_url}/search/movie"
        params = {
            "query": title,
            "include_adult": "false",
        }
        if year:
            params["year"] = year

        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[TMDb] HTTP {resp.status_code} while searching '{title}'")
            return None

        data = resp.json()
        results = data.get("results") or []
        if not results:
            return None

        return results[0]

    def get_movie_details(self, movie_id: int) -> Optional[dict]:
        """
        Optional helper for full details (not strictly needed now).
        """
        url = f"{self.base_url}/movie/{movie_id}"
        resp = self.session.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        return resp.json()


# -----------------------------------------------------------------------------
# RandomForestPreferencePredictor
# -----------------------------------------------------------------------------
class RandomForestPreferencePredictor:
    """
    Per-user model that learns to predict preference for movies based on:
      - Letterboxd explicit ratings
      - TMDb metadata (genre_ids, year, vote_average, popularity)

    Output score is in range ~0.0–2.0, where 1.0 is neutral.
    """

    def __init__(self, n_estimators: int = 200, random_state: int = 42):
        self.rf_model: Optional[RandomForestRegressor] = None
        self.genre_weights: Dict[int, float] = {}  # Kept for fallback/cold-start
        self.prefs_index: Dict[Tuple[str, Optional[int]], MoviePreference] = {}
        self.n_estimators = n_estimators
        self.random_state = random_state

        # Feature metadata
        self.genre_vocab: Dict[int, int] = {}  # genre_id -> feature index
        self.feature_names: List[str] = []
        self.mean_rating = 1.0  # neutral (0-2 scale)

    def _normalize_title(self, title: str) -> str:
        # Use same normalization globally
        return normalize_title_global(title)

    def _extract_features(self, tmdb_data: Optional[dict]) -> List[float]:
        """Convert TMDB data to numeric feature vector."""
        if not tmdb_data:
            return [0.0] * len(self.feature_names) if self.feature_names else [0.0]

        # If we somehow have no feature names, fall back to simple 1D feature
        if not self.feature_names:
            return self._fallback_features(tmdb_data)

        features = [0.0] * len(self.feature_names)

        # Genre features (one-hot encoded)
        genre_ids = tmdb_data.get("genre_ids", [])
        for gid in genre_ids:
            if gid in self.genre_vocab:
                idx = self.genre_vocab[gid]
                features[idx] = 1.0

        # Numeric features (add more as needed)
        year = tmdb_data.get("release_date", "")[:4]
        if year and year.isdigit():
            # Normalize year to 0-1 (1980-2025 range)
            year_feat = (int(year) - 1980) / 45.0
            if "year" in self.feature_names:
                features[self.feature_names.index("year")] = year_feat

        # TMDb vote average (0-10 -> 0-1)
        vote_avg = tmdb_data.get("vote_average", 0)
        if vote_avg and "vote_avg" in self.feature_names:
            features[self.feature_names.index("vote_avg")] = vote_avg / 10.0

        # Popularity (log scale)
        popularity = tmdb_data.get("popularity", 0)
        if popularity and "popularity" in self.feature_names:
            features[self.feature_names.index("popularity")] = np.log1p(popularity) / 10.0

        return features

    def _fallback_features(self, tmdb_data: dict) -> List[float]:
        """Simple fallback when model isn't trained."""
        genre_ids = tmdb_data.get("genre_ids", [])
        if not genre_ids:
            return [0.0]

        # Average genre weight
        weights = [self.genre_weights.get(gid, 0.0) for gid in genre_ids]
        return [sum(weights) / len(genre_ids)]

    def _build_feature_vocab(self, all_tmdb_data: List[dict]):
        """Build feature vocabulary from all available movies."""
        all_genres = set()
        for data in all_tmdb_data:
            all_genres.update(data.get("genre_ids", []))

        # Create genre vocab
        self.genre_vocab = {gid: i for i, gid in enumerate(sorted(all_genres))}

        # Feature names
        self.feature_names = [f"genre_{gid}" for gid in sorted(all_genres)]
        self.feature_names.extend(["year", "vote_avg", "popularity"])

    def train(self, movie_features: Dict[Tuple[str, Optional[int]], dict]):
        """
        Train Random Forest on user's explicit ratings.

        movie_features: {(norm_title, year): tmdb_data}
        """
        if not self.prefs_index:
            return

        # Build feature vocab from all available movies
        self._build_feature_vocab(list(movie_features.values()))

        X, y = [], []
        for (norm_title, year), pref in self.prefs_index.items():
            if pref.rating is not None and pref.rating > 0:
                tmdb_data = movie_features.get((norm_title, year), {})
                features = self._extract_features(tmdb_data)
                X.append(features)
                y.append(pref.rating / 5.0 * 2.0)  # 0-2 scale

        if len(X) < 5:
            # Too few samples → fall back to simple genre weights
            self._learn_genre_weights(movie_features)
            self.mean_rating = 1.0
            print("[RF] Not enough data to train RF, using genre-weight fallback.")
            return

        # Train model
        self.rf_model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            max_depth=10,
            min_samples_split=3,
            min_samples_leaf=2,
        )
        self.rf_model.fit(X, y)
        self.mean_rating = float(np.mean(y))

        # Keep genre weights as fallback
        self._learn_genre_weights(movie_features)

        print(
            f"[RF] Trained RandomForest with {len(X)} samples. "
            f"Mean target={self.mean_rating:.3f}"
        )

    def _learn_genre_weights(self, movie_features: Dict[Tuple[str, Optional[int]], dict]):
        """Fallback: learn simple genre weights like original approach."""
        genre_scores: Dict[int, float] = {}
        genre_counts: Dict[int, int] = {}

        for (norm_title, year), pref in self.prefs_index.items():
            if pref.rating is None:
                continue

            tmdb_data = movie_features.get((norm_title, year), {})
            genre_ids = tmdb_data.get("genre_ids", [])
            normalized_rating = pref.rating / 5.0 * 2.0

            for gid in genre_ids:
                genre_scores[gid] = genre_scores.get(gid, 0) + normalized_rating
                genre_counts[gid] = genre_counts.get(gid, 0) + 1

        self.genre_weights = {
            gid: score / max(genre_counts.get(gid, 1), 1)
            for gid, score in genre_scores.items()
        }

    def predict_preference(
        self,
        movie_title: str,
        movie_year: Optional[int],
        tmdb_data: Optional[dict],
    ) -> float:
        """
        Predict preference using Random Forest with explicit-rating fallback.
        Returns score in range ~0.0 - 2.0.
        """
        # 1) Explicit rating fallback
        norm_title = self._normalize_title(movie_title)
        explicit = self.prefs_index.get((norm_title, movie_year)) or \
                   self.prefs_index.get((norm_title, None))

        if explicit and explicit.rating is not None:
            return explicit.rating / 5.0 * 2.0

        # 2) Random Forest prediction
        if self.rf_model and tmdb_data:
            try:
                features = self._extract_features(tmdb_data)
                rf_score = self.rf_model.predict([features])[0]
                return float(np.clip(rf_score, 0.0, 2.0))
            except Exception as e:
                print(f"[RF] Prediction failed for '{movie_title}': {e}")

        # 3) Genre-weight fallback (cold start)
        if tmdb_data and self.genre_weights:
            genre_ids = tmdb_data.get("genre_ids", [])
            if genre_ids:
                weights = [self.genre_weights.get(gid, 0.0) for gid in genre_ids]
                denom = max(
                    len(genre_ids),
                    1
                ) * (abs(max(self.genre_weights.values(), default=1.0)) + 1e-6)
                return float(sum(weights) / denom)

        # 4) Default neutral score
        return float(self.mean_rating)

    def save_model(self, filepath: str):
        """Persist model to disk."""
        with open(filepath, "wb") as f:
            pickle.dump(
                {
                    "rf_model": self.rf_model,
                    "genre_weights": self.genre_weights,
                    "genre_vocab": self.genre_vocab,
                    "feature_names": self.feature_names,
                    "mean_rating": self.mean_rating,
                },
                f,
            )

    def load_model(self, filepath: str):
        """Load model from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.rf_model = data["rf_model"]
            self.genre_weights = data["genre_weights"]
            self.genre_vocab = data["genre_vocab"]
            self.feature_names = data["feature_names"]
            self.mean_rating = data["mean_rating"]


# -----------------------------------------------------------------------------
# UserTasteProfile: wraps RF model per user
# -----------------------------------------------------------------------------
@dataclass
class UserTasteProfile:
    username: str
    rf_predictor: RandomForestPreferencePredictor

    def predict_preference(
        self,
        movie_title: str,
        movie_year: Optional[int],
        tmdb_data: Optional[dict],
    ) -> float:
        return self.rf_predictor.predict_preference(movie_title, movie_year, tmdb_data)

    @classmethod
    def from_letterboxd(
        cls,
        username: str,
        lb_integration: LetterboxdIntegration,
        tmdb_client: TMDbClient,
    ) -> "UserTasteProfile":
        """
        Build a per-user RandomForest preference model from Letterboxd history.
        """
        print(f"[UserTasteProfile] Building profile for '{username}'")
        prefs = lb_integration.get_preferences()

        # 1) Build prefs_index with normalized titles
        prefs_index: Dict[Tuple[str, Optional[int]], MoviePreference] = {}
        movie_features: Dict[Tuple[str, Optional[int]], dict] = {}

        for p in prefs:
            if p.rating is None:
                continue

            norm_title = normalize_title_global(p.title)
            key = (norm_title, p.year)

            # Keep highest rating if duplicates
            old = prefs_index.get(key)
            if (not old) or (old.rating is None) or (p.rating > old.rating):
                prefs_index[key] = p

            # Fetch TMDb metadata once per (title, year)
            if key not in movie_features:
                try:
                    meta = tmdb_client.search_movie(p.title, p.year)
                except Exception:
                    meta = None
                if meta:
                    movie_features[key] = meta

        rf = RandomForestPreferencePredictor()
        rf.prefs_index = prefs_index
        rf.train(movie_features)

        return cls(
            username=username,
            rf_predictor=rf,
        )


# -----------------------------------------------------------------------------
# Output dataclasses for group matching
# -----------------------------------------------------------------------------
@dataclass
class ShowTime:
    cinema: str
    start: datetime


@dataclass
class GroupMatchedMovie:
    title: str
    year: Optional[int]
    group_score: float
    per_user_scores: Dict[str, float]
    showtimes: List[ShowTime]  # flattened time+location (only inside free slots)
    cineville: dict
    tmdb: Optional[dict]


# -----------------------------------------------------------------------------
# Calendar-based showtime filtering
# -----------------------------------------------------------------------------
def filter_movie_schedules_by_free_slots(
    cineville_movie: dict,
    free_slots: List[Tuple[datetime, datetime]],
    buffer_minutes: int = 30,
    max_end_overrun_minutes: int = 0,
    max_start_advance_minutes: int = 0,
    allow_start_inside: bool = False,
) -> dict:
    """
    Given a Cineville movie dict with:
        {
          'title': ...,
          'year': ...,
          'duration': int | None,
          'schedules': { 'Cinema': [datetime, ...], ... }
        }

    return a **new schedules dict** containing only showtimes that
    fully fit inside any of the free intervals from the calendar.

    If no showtime fits, the returned dict is empty.
    """
    original_schedules = cineville_movie.get("schedules", {}) or {}
    if not original_schedules or not free_slots:
        return {}

    duration = cineville_movie.get("duration") or 120  # default 2h
    buffer = timedelta(minutes=buffer_minutes)

    # Determine system local timezone info (may be None on some installs)
    try:
        local_tz = datetime.now().astimezone().tzinfo
    except Exception:
        local_tz = None

    # Debugging toggle (set env SHOWTIME_DEBUG=1 to enable)
    debug = bool(os.getenv("SHOWTIME_DEBUG", ""))
    if debug:
        print(f"[ShowtimeDebug] Movie='{cineville_movie.get('title')}' year={cineville_movie.get('year')}")
        print(f"[ShowtimeDebug] Free slots ({len(free_slots)}):")
        for s, e in free_slots:
            print(f"  - slot start={s} end={e} tz={getattr(s,'tzinfo',None)}")

    filtered: Dict[str, List[datetime]] = {}

    for cinema, times in original_schedules.items():
        for showtime in times:
            if not isinstance(showtime, datetime):
                continue

            # Convert showtime to local timezone (if showtime is aware).
            # Then compare as naive local datetimes so they match calendar free slots
            if showtime.tzinfo is not None and local_tz is not None:
                try:
                    st_local = showtime.astimezone(local_tz).replace(tzinfo=None)
                except Exception:
                    st_local = showtime.replace(tzinfo=None)
            else:
                st_local = showtime.replace(tzinfo=None)

            if debug:
                print(f"[ShowtimeDebug]   showtime original={showtime} tz={getattr(showtime,'tzinfo',None)} -> st_local={st_local}")

            movie_end_local = st_local + timedelta(minutes=duration) + buffer

            # Check if this show fits entirely inside any free slot
            fits_any_slot = False
            for slot_start, slot_end in free_slots:
                # If slot_start/slot_end are timezone-aware, convert them to naive local too
                if getattr(slot_start, "tzinfo", None) is not None and local_tz is not None:
                    try:
                        slot_start_local = slot_start.astimezone(local_tz).replace(tzinfo=None)
                        slot_end_local = slot_end.astimezone(local_tz).replace(tzinfo=None)
                    except Exception:
                        slot_start_local = slot_start.replace(tzinfo=None)
                        slot_end_local = slot_end.replace(tzinfo=None)
                else:
                    slot_start_local = slot_start
                    slot_end_local = slot_end

                if debug:
                    print(f"[ShowtimeDebug]     comparing st_local={st_local} movie_end_local={movie_end_local} against slot_start={slot_start_local} slot_end={slot_end_local}")

                # Option: accept if the movie STARTS within the slot even if it ends after it
                if allow_start_inside and (st_local >= slot_start_local and st_local <= slot_end_local):
                    fits_any_slot = True
                    if debug:
                        print("[ShowtimeDebug]     => FITS slot (start inside, end may overrun)")
                    break

                # Allow a small start advance (movie starts slightly before slot)
                allowed_start_local = slot_start_local - timedelta(minutes=max_start_advance_minutes)
                # Allow a small end overrun (movie ends slightly after slot)
                allowed_end_local = slot_end_local + timedelta(minutes=max_end_overrun_minutes)

                if debug:
                    print(f"[ShowtimeDebug]     allowed_start={allowed_start_local} allowed_end={allowed_end_local} (start_adv={max_start_advance_minutes} end_overrun={max_end_overrun_minutes})")

                if st_local >= allowed_start_local and movie_end_local <= allowed_end_local:
                    fits_any_slot = True
                    if debug:
                        print("[ShowtimeDebug]     => FITS slot (within tolerances)")
                    break

            if debug and not fits_any_slot:
                print("[ShowtimeDebug]   => does NOT fit any slot")

            if fits_any_slot:
                filtered.setdefault(cinema, []).append(showtime)

    # Sort times per cinema
    for c, ts in filtered.items():
        filtered[c] = sorted(ts)

    return filtered


# -----------------------------------------------------------------------------
# GroupMovieMatcher
# -----------------------------------------------------------------------------
class GroupMovieMatcher:
    """
    Group-level recommender using learned taste profiles AND calendar availability.

    Usage from project root:

        $env:LETTERBOXD_USERNAMES="user1,user2"
        python -m src.movie_matcher
    """

    def __init__(self, cineville_scraper: CinevilleScraper, tmdb_client: TMDbClient):
        self.cineville_scraper = cineville_scraper
        self.tmdb_client = tmdb_client

    def match_group(
    self,
    usernames: List[str],
    days_ahead: int = 7,
    limit_amsterdam: bool = True,
    max_results: int = 20,
    use_calendar: bool = True,
    min_slot_minutes: int = 120,
    mood: Optional[str] = None,
    learn_from_history: bool = True,
) -> List[GroupMatchedMovie]:
        """Main entry point"""
        # Initialize group history
        group_id = create_group_id(usernames)
        group_history = GroupHistory(group_id=group_id)
        
        # Show group summary
        summary = group_history.get_group_summary()
        print(f" Group: {group_id}")
        print(f" {summary['message']}")
        
        # 1) Build taste profiles
        profiles: List[UserTasteProfile] = []
        for u in usernames:
            u = u.strip()
            if not u:
                continue
            lb = LetterboxdIntegration(username=u)
            profile = UserTasteProfile.from_letterboxd(
                username=u,
                lb_integration=lb,
                tmdb_client=self.tmdb_client,
            )
            profiles.append(profile)

        if not profiles:
            print("[GroupMovieMatcher] No valid users, aborting.")
            return [], group_history  # Changed from: return []
            return [], group_history

        # 2) Get calendar free slots FIRST
        free_slots: Optional[List[Tuple[datetime, datetime]]] = None
        if use_calendar:
            try:
                free_slots = find_common_available_times(
                    days_ahead=days_ahead,
                    min_duration_minutes=min_slot_minutes,
                )
                print(f"[GroupMovieMatcher] Found {len(free_slots)} common free slots.")
                
                # Debug: show the slot dates
                if free_slots:
                    print(f"   First slot: {free_slots[0][0]} - {free_slots[0][1]}")
                    print(f"   Last slot: {free_slots[-1][0]} - {free_slots[-1][1]}")
            except Exception as e:
                print(f"[GroupMovieMatcher] Error getting free slots: {e}")
                print(f"[GroupMovieMatcher] Falling back to no calendar filtering")
                free_slots = None  # Continue without calendar filtering
        
        # 3) Get Cineville movies
        # If we don't have free slots, get ALL movies and don't filter by calendar
        print("\n[GroupMovieMatcher] Fetching Cineville movies...")
        if free_slots:
            print(f"[GroupMovieMatcher] Using {len(free_slots)} free calendar slots")
            cineville_movies = self.cineville_scraper.get_movies_for_free_slots(
                free_slots=free_slots,
                limit_amsterdam=limit_amsterdam
            )
        else:
            print("[GroupMovieMatcher] No calendar filtering - showing all movies")
            # Get all movies for the next days_ahead days
            all_showtimes = self.cineville_scraper.get_all_showtimes(
                days_ahead=days_ahead,
                limit_amsterdam=limit_amsterdam
            )
            # Group by movie title
            movies_dict = {}
            for showtime in all_showtimes:
                title = showtime.get('title')
                if title not in movies_dict:
                    movies_dict[title] = {
                        'title': title,
                        'year': showtime.get('year'),
                        'schedules': {}
                    }
                cinema = showtime.get('cinema', 'Unknown')
                if cinema not in movies_dict[title]['schedules']:
                    movies_dict[title]['schedules'][cinema] = []
                movies_dict[title]['schedules'][cinema].append(showtime.get('showtime'))
            
            cineville_movies = list(movies_dict.values())

        if not cineville_movies:
            print("[GroupMovieMatcher] No Cineville movies found in free slots.")
            return [], group_history
            print("[GroupMovieMatcher] No Cineville movies found.")
            return [], group_history

        print(f"[GroupMovieMatcher] Found {len(cineville_movies)} movies")

        # 4) Score and rank movies
        results: List[GroupMatchedMovie] = []

        for movie in cineville_movies:
            title = movie.get("title")
            year = movie.get("year")

            if not title:
                continue

            # Now we don't need to filter schedules - they're already filtered!
            # All showtimes are guaranteed to be in free slots

            # TMDb metadata
            try:
                tmdb_data = self.tmdb_client.search_movie(title, year)
            except Exception:
                tmdb_data = None

            # Per-user RF scores
            per_user_scores: Dict[str, float] = {}
            for profile in profiles:
                s = profile.predict_preference(title, year, tmdb_data)
                per_user_scores[profile.username] = s

            if not per_user_scores:
                continue

            scores_list = list(per_user_scores.values())
            avg_score = sum(scores_list) / len(scores_list)
            worst = min(scores_list)
            best = max(scores_list)
            
            # Group score formula with better differentiation
            # Scale: 0.0 - 2.0 (like individual scores)
            # More weight on worst score to heavily penalize if someone dislikes it
            # Also consider variance - movies everyone agrees on get a bonus
            variance_penalty = (best - worst) * 0.2  # Penalize disagreement
            
            # 50% average, 40% worst (fairness), -10% variance penalty
            group_score = 0.5 * avg_score + 0.4 * worst - variance_penalty
            
            # Clamp to valid range [0.0, 2.0]
            group_score = max(0.0, min(2.0, group_score))

            # Flatten showtimes
            showtimes: List[ShowTime] = []
            for cinema, times in movie.get("schedules", {}).items():
                for t in times:
                    showtimes.append(ShowTime(cinema=cinema, start=t))

            if not showtimes:
                continue

            showtimes.sort(key=lambda st: st.start)

            results.append(
                GroupMatchedMovie(
                    title=title,
                    year=year,
                    group_score=float(group_score),
                    per_user_scores=per_user_scores,
                    showtimes=showtimes,
                    cineville=movie,
                    tmdb=tmdb_data,
                )
            )
        # APPLY MOOD FILTER (if provided)
        if mood:
            mood_filter = MoodFilter()
            results = mood_filter.apply_mood(results, mood=mood, aggressive=False)
            
        # APPLY GROUP LEARNING (if enabled and history exists)
        if learn_from_history and len(group_history.history) > 0:
            results = group_history.apply_learning(results, usernames)
        
        # NORMALIZE SCORES for better differentiation
        # This spreads the scores across the full range to make differences more visible
        if results:
            scores = [r.group_score for r in results]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            # Only normalize if there's enough variation
            if score_range > 0.1:  # At least 0.1 difference
                for r in results:
                    # Normalize to 0-2 range with some minimum floor
                    # Keep minimum at 0.4 (20% on 0-10 scale) so nothing shows as 0
                    normalized = ((r.group_score - min_score) / score_range) * 1.6 + 0.4
                    r.group_score = float(normalized)
            
        # Sort and return
        results.sort(key=lambda r: r.group_score, reverse=True)
        if max_results and max_results > 0:
            results = results[:max_results]
            
        return results, group_history


# -----------------------------------------------------------------------------
# CLI Test
# -----------------------------------------------------------------------------
def _test_group_matcher():
    """
    Run group matcher from CLI.

    Env vars:
      - LETTERBOXD_USERNAMES   e.g. "visionofdavinci,friend1"
      - (TMDB_API_KEY is embedded in this file but can also be overridden via env)
    """
    usernames_raw = os.getenv("LETTERBOXD_USERNAMES", "")
    usernames = [u.strip() for u in usernames_raw.split(",") if u.strip()]

    if not usernames:
        print("Set LETTERBOXD_USERNAMES='user1,user2' to test group matcher.")
        return

    print(f"[CLI] Using users: {', '.join(usernames)}")

    cineville = CinevilleScraper()
    tmdb = TMDbClient(api_key=TMDB_API_KEY)

    matcher = GroupMovieMatcher(cineville, tmdb)
    # Allow disabling calendar filtering for debugging via env var USE_CALENDAR (0/1)
    use_cal_str = os.getenv("USE_CALENDAR", "1")
    use_calendar_flag = False if use_cal_str in ("0", "false", "False") else True

    results, group_history = matcher.match_group(
        usernames=usernames,
        days_ahead=3,
        limit_amsterdam=True,
        max_results=10,
        use_calendar=use_calendar_flag,
        min_slot_minutes=120,
    )

    print("\n=== Group Recommendations (only within free calendar slots) ===\n")
    for i, r in enumerate(results, start=1):
        print(f"{i:2d}. {r.title} ({r.year or '?'})  group={r.group_score:.3f}")
        for u, s in r.per_user_scores.items():
            print(f"      {u}: {s:.3f}")

        # Show first few showtimes that actually fit in free slots
        for st in r.showtimes[:3]:
            print(f"      {st.cinema} @ {st.start.strftime('%a %d %b %H:%M')}")
        if len(r.showtimes) > 3:
            print(f"      (+ {len(r.showtimes) - 3} more showtimes)")
        print()


if __name__ == "__main__":
    _test_group_matcher()
