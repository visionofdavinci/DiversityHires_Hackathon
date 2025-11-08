"""
movie_matcher.py

Group movie matching with learned personal profiles.

- For each user:
    - Pull ratings from Letterboxd (via LetterboxdIntegration)
    - Pull metadata for rated movies from TMDb
    - Train a RandomForestRegressor to predict preference for new movies

- For a group of users:
    - For each Cineville movie (title + year), get TMDb data
    - Predict a preference score per user
    - Combine into a group score
    - Return ranked group recommendations including:
        - title, year
        - per-user scores
        - group score
        - showtimes (cinema + datetime)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
from typing import Dict, List, Optional, Tuple, Any

import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

TMDB_API_KEY = "0ad625d2ef7503df5817998ca55e0bdf"

# -----------------------------------------------------------------------------
# Robust imports for local modules (cineville_scraper + letterboxd_integration)
# -----------------------------------------------------------------------------
try:
    # When run as a module: python -m src.movie_matcher
    from .cineville_scraper import CinevilleScraper
    from .letterboxd_integration import LetterboxdIntegration, MoviePreference
except ImportError:
    # When run as a script: python src/movie_matcher.py
    import sys

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(CURRENT_DIR)
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)

    from cineville_scraper import CinevilleScraper
    from letterboxd_integration import LetterboxdIntegration, MoviePreference


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

    Expects TMDb API key in:
        - env var TMDB_API_KEY
      or
        - passed explicitly to the constructor.
    """

    def __init__(self, api_key = TMDB_API_KEY, language: str = "en-US") -> None:
        # Prefer explicit, fallback to env var
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

        print(f"[RF] Trained RandomForest with {len(X)} samples. "
              f"Mean target={self.mean_rating:.3f}")

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
    showtimes: List[ShowTime]  # flattened time+location
    cineville: dict
    tmdb: Optional[dict]


# -----------------------------------------------------------------------------
# GroupMovieMatcher
# -----------------------------------------------------------------------------
class GroupMovieMatcher:
    """
    Group-level recommender using learned taste profiles for multiple users.

    Usage from project root:

        $env:TMDB_API_KEY="..."
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
    ) -> List[GroupMatchedMovie]:
        # 1) Build a Letterboxd + taste profile per user
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
            return []

        # 2) Get Cineville movies
        cineville_movies = self.cineville_scraper.get_movies_with_schedule(
            days_ahead=days_ahead,
            limit_amsterdam=limit_amsterdam,
        )

        if not cineville_movies:
            print("[GroupMovieMatcher] No Cineville movies found.")
            return []

        # 3) For each movie, compute TMDb data once and user scores
        results: List[GroupMatchedMovie] = []

        for movie in cineville_movies:
            title = movie.get("title")
            year = movie.get("year")

            if not title:
                continue

            try:
                tmdb_data = self.tmdb_client.search_movie(title, year)
            except Exception:
                tmdb_data = None

            per_user_scores: Dict[str, float] = {}
            for profile in profiles:
                s = profile.predict_preference(title, year, tmdb_data)
                per_user_scores[profile.username] = s

            if not per_user_scores:
                continue

            scores_list = list(per_user_scores.values())
            avg_score = sum(scores_list) / len(scores_list)
            worst = min(scores_list)
            # Group score: average + penalty if someone really dislikes it
            group_score = avg_score + 0.3 * worst

            # 4) Flatten showtimes (time + location)
            showtimes: List[ShowTime] = []
            for cinema, times in movie.get("schedules", {}).items():
                for t in times:
                    showtimes.append(ShowTime(cinema=cinema, start=t))

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

        # 5) Sort by group score and trim
        results.sort(key=lambda r: r.group_score, reverse=True)
        if max_results and max_results > 0:
            results = results[:max_results]

        return results


# -----------------------------------------------------------------------------
# CLI Test
# -----------------------------------------------------------------------------
def _test_group_matcher():
    """
    Run group matcher from CLI.

    Env vars:
      - TMDB_API_KEY           (required)
      - LETTERBOXD_USERNAMES   e.g. "visionofdavinci,friend1"
    """
    tmdb_key = TMDB_API_KEY
    if not tmdb_key:
        print("Please set TMDB_API_KEY before running.")
        return

    usernames_raw = os.getenv("LETTERBOXD_USERNAMES", "")
    usernames = [u.strip() for u in usernames_raw.split(",") if u.strip()]

    if not usernames:
        print("Set LETTERBOXD_USERNAMES='user1,user2' to test group matcher.")
        return

    print(f"[CLI] Using users: {', '.join(usernames)}")

    cineville = CinevilleScraper()
    tmdb = TMDbClient(api_key=tmdb_key)

    matcher = GroupMovieMatcher(cineville, tmdb)
    results = matcher.match_group(
        usernames=usernames,
        days_ahead=3,
        limit_amsterdam=True,
        max_results=10,
    )

    print("\n=== Group Recommendations ===\n")
    for i, r in enumerate(results, start=1):
        print(f"{i:2d}. {r.title} ({r.year or '?'})  group={r.group_score:.3f}")
        for u, s in r.per_user_scores.items():
            print(f"      {u}: {s:.3f}")
        # Show first few showtimes
        for st in r.showtimes[:3]:
            print(f"      {st.cinema} @ {st.start.strftime('%a %d %b %H:%M')}")
        if len(r.showtimes) > 3:
            print(f"      (+ {len(r.showtimes) - 3} more showtimes)")
        print()


if __name__ == "__main__":
    _test_group_matcher()
