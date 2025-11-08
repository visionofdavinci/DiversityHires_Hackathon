"""
group_history.py

Track group movie choices and learn preferences over time.
Enables:
- Learning from past choices
- Fair rotation (ensure everyone gets their favorites)
- Diversity bonus (avoid repeating same genres)
- Group compatibility insights
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class GroupChoice:
    """Record of a single group movie choice"""
    timestamp: str
    group_members: List[str]
    options: List[Dict[str, Any]]  # All recommendations shown
    chosen_title: str
    chosen_year: Optional[int]
    chosen_genres: List[int]  # TMDb genre IDs
    per_user_scores: Dict[str, float]  # How each user felt about the choice


class GroupHistory:
    """
    Track and learn from a group's movie choices over time
    
    Features:
    - Records what movies were chosen
    - Learns preferred genres, cinemas, times
    - Ensures fair rotation between members
    - Boosts diversity to avoid repetition
    """
    
    def __init__(self, group_id: str, history_dir: str = "data/groups"):
        """
        Initialize group history
        
        Args:
            group_id: Unique identifier for this group (e.g., "alice_bob_charlie")
            history_dir: Directory to store history files
        """
        self.group_id = group_id
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / f"{group_id}_history.json"
        self.preferences_file = self.history_dir / f"{group_id}_preferences.json"
        
        self.history: List[Dict] = []
        self.preferences: Dict = {
            'preferred_genres': {},  # genre_id -> count
            'preferred_cinemas': {},  # cinema -> count
            'preferred_times': [],  # list of preferred hour ranges
            'user_satisfaction': {},  # user -> cumulative satisfaction
            'total_sessions': 0
        }
        
        self.load_history()
        self.load_preferences()
    
    def load_history(self):
        """Load history from disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                print(f"📚 Loaded {len(self.history)} past choices for group {self.group_id}")
            except Exception as e:
                print(f"⚠️ Error loading history: {e}")
                self.history = []
    
    def load_preferences(self):
        """Load learned preferences from disk"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    self.preferences = json.load(f)
                print(f"🧠 Loaded learned preferences for group {self.group_id}")
            except Exception as e:
                print(f"⚠️ Error loading preferences: {e}")
    
    def save_history(self):
        """Save history to disk"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
    
    def save_preferences(self):
        """Save preferences to disk"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving preferences: {e}")
    
    def record_choice(
        self,
        group_members: List[str],
        all_recommendations: List[Any],  # List[GroupMatchedMovie]
        chosen_movie: Any,  # GroupMatchedMovie
    ):
        """
        Record what the group chose
        
        Args:
            group_members: List of usernames in the group
            all_recommendations: All movies that were recommended
            chosen_movie: The movie the group actually picked
        """
        
        print(f"\n📝 Recording choice: {chosen_movie.title}")
        
        # Extract genres from chosen movie
        chosen_genres = []
        if chosen_movie.tmdb:
            chosen_genres = chosen_movie.tmdb.get('genre_ids', [])
        
        # Record the choice
        choice_record = {
            'timestamp': datetime.now().isoformat(),
            'group_members': sorted(group_members),
            'chosen_title': chosen_movie.title,
            'chosen_year': chosen_movie.year,
            'chosen_genres': chosen_genres,
            'chosen_score': chosen_movie.group_score,
            'per_user_scores': chosen_movie.per_user_scores,
            'chosen_cinema': chosen_movie.showtimes[0].cinema if chosen_movie.showtimes else None,
            'chosen_time': chosen_movie.showtimes[0].start.isoformat() if chosen_movie.showtimes else None,
            'all_options': [
                {
                    'title': r.title,
                    'year': r.year,
                    'group_score': r.group_score,
                    'per_user_scores': r.per_user_scores
                }
                for r in all_recommendations[:10]  # Store top 10
            ]
        }
        
        self.history.append(choice_record)
        self.save_history()
        
        # Update learned preferences
        self._update_preferences(choice_record)
        
        print(f"✅ Recorded! Total history: {len(self.history)} choices")
    
    def _update_preferences(self, choice_record: Dict):
        """Learn from this choice to update preferences"""
        
        # Update genre preferences
        for genre_id in choice_record['chosen_genres']:
            genre_id_str = str(genre_id)
            self.preferences['preferred_genres'][genre_id_str] = \
                self.preferences['preferred_genres'].get(genre_id_str, 0) + 1
        
        # Update cinema preferences
        if choice_record['chosen_cinema']:
            cinema = choice_record['chosen_cinema']
            self.preferences['preferred_cinemas'][cinema] = \
                self.preferences['preferred_cinemas'].get(cinema, 0) + 1
        
        # Update time preferences
        if choice_record['chosen_time']:
            chosen_dt = datetime.fromisoformat(choice_record['chosen_time'])
            hour = chosen_dt.hour
            self.preferences['preferred_times'].append(hour)
        
        # Update user satisfaction
        for user, score in choice_record['per_user_scores'].items():
            self.preferences['user_satisfaction'][user] = \
                self.preferences['user_satisfaction'].get(user, 0.0) + score
        
        self.preferences['total_sessions'] += 1
        
        self.save_preferences()
    
    def get_underrepresented_users(self, current_members: List[str]) -> List[str]:
        """
        Find users whose preferences haven't been satisfied lately
        
        Returns:
            List of usernames who deserve priority
        """
        if self.preferences['total_sessions'] < 2:
            return []  # Not enough data
        
        satisfaction = self.preferences['user_satisfaction']
        
        # Only consider current members
        current_satisfaction = {
            user: satisfaction.get(user, 0.0)
            for user in current_members
        }
        
        if not current_satisfaction:
            return []
        
        avg_satisfaction = np.mean(list(current_satisfaction.values()))
        
        # Find users below 80% of average
        underrepresented = [
            user for user, score in current_satisfaction.items()
            if score < avg_satisfaction * 0.8
        ]
        
        return underrepresented
    
    def get_recent_genres(self, last_n: int = 3) -> set:
        """Get genres from last N movies to avoid repetition"""
        recent_genres = set()
        
        for choice in self.history[-last_n:]:
            recent_genres.update(choice.get('chosen_genres', []))
        
        return recent_genres
    
    def apply_learning(
        self,
        recommendations: List[Any],  # List[GroupMatchedMovie]
        current_members: List[str]
    ) -> List[Any]:
        """
        Apply learned preferences to boost/penalize recommendations
        
        This is the main method that makes the bot "smarter"
        
        Args:
            recommendations: List of GroupMatchedMovie objects
            current_members: Current group members
        
        Returns:
            Adjusted list of recommendations
        """
        
        if self.preferences['total_sessions'] < 1:
            print("First time with this group - no history to learn from yet")
            return recommendations
        
        print(f"\n Applying learned preferences from {len(self.history)} past choices...")
        
        # 1. Fair Rotation - boost movies for underrepresented users
        underrepresented = self.get_underrepresented_users(current_members)
        if underrepresented:
            print(f"    Fair rotation: Boosting for {', '.join(underrepresented)}")
            recommendations = self._apply_fair_rotation(recommendations, underrepresented)
        
        # 2. Diversity Bonus - avoid recent genres
        recent_genres = self.get_recent_genres(last_n=3)
        if recent_genres:
            print(f"    Diversity boost: Avoiding genres {recent_genres}")
            recommendations = self._apply_diversity_bonus(recommendations, recent_genres)
        
        # 3. Cinema Preferences - boost preferred cinemas
        if self.preferences['preferred_cinemas']:
            print(f"    Cinema preferences: {list(self.preferences['preferred_cinemas'].keys())[:3]}")
            recommendations = self._apply_cinema_preferences(recommendations)
        
        # 4. Genre Preferences - boost preferred genres
        if self.preferences['preferred_genres']:
            print(f"    Genre preferences learned")
            recommendations = self._apply_genre_preferences(recommendations)
        
        # Re-sort by adjusted scores
        recommendations.sort(key=lambda r: r.group_score, reverse=True)
        
        print(f"Applied learning! Top recommendation boosted by preferences\n")
        
        return recommendations
    
    def _apply_fair_rotation(
        self,
        recommendations: List[Any],
        underrepresented_users: List[str]
    ) -> List[Any]:
        """Boost movies that underrepresented users will love"""
        
        for movie in recommendations:
            for user in underrepresented_users:
                if user in movie.per_user_scores:
                    user_score = movie.per_user_scores[user]
                    
                    if user_score > 1.5:  # User really likes this movie
                        boost = 0.4
                        movie.group_score += boost
                        
                        if not hasattr(movie, 'boost_reasons'):
                            movie.boost_reasons = []
                        movie.boost_reasons.append(
                            f"{user}'s turn to pick! "
                        )
        
        return recommendations
    
    def _apply_diversity_bonus(
        self,
        recommendations: List[Any],
        recent_genres: set
    ) -> List[Any]:
        """Boost movies with different genres than recent choices"""
        
        for movie in recommendations:
            if not movie.tmdb:
                continue
            
            movie_genres = set(movie.tmdb.get('genre_ids', []))
            overlap = len(movie_genres & recent_genres)
            
            if overlap == 0:
                # Completely different genres!
                boost = 0.5
                movie.group_score += boost
                
                if not hasattr(movie, 'boost_reasons'):
                    movie.boost_reasons = []
                movie.boost_reasons.append("Fresh pick! 🌟")
            
            elif overlap <= 1:
                # Some variety
                boost = 0.2
                movie.group_score += boost
                
                if not hasattr(movie, 'boost_reasons'):
                    movie.boost_reasons = []
                movie.boost_reasons.append("Nice variety ✨")
        
        return recommendations
    
    def _apply_cinema_preferences(self, recommendations: List[Any]) -> List[Any]:
        """Boost movies at preferred cinemas"""
        
        total_visits = sum(self.preferences['preferred_cinemas'].values())
        
        for movie in recommendations:
            if not movie.showtimes:
                continue
            
            # Check if any showtime is at a preferred cinema
            for showtime in movie.showtimes:
                cinema = showtime.cinema
                visit_count = self.preferences['preferred_cinemas'].get(cinema, 0)
                
                if visit_count > 0:
                    # Boost proportional to how often they've gone there
                    boost = 0.3 * (visit_count / total_visits)
                    movie.group_score += boost
                    break  # Only boost once per movie
        
        return recommendations
    
    def _apply_genre_preferences(self, recommendations: List[Any]) -> List[Any]:
        """Boost movies in preferred genres"""
        
        total_genre_picks = sum(self.preferences['preferred_genres'].values())
        
        for movie in recommendations:
            if not movie.tmdb:
                continue
            
            movie_genres = movie.tmdb.get('genre_ids', [])
            
            # Calculate genre preference score
            genre_score = 0
            for genre_id in movie_genres:
                genre_id_str = str(genre_id)
                pick_count = self.preferences['preferred_genres'].get(genre_id_str, 0)
                
                if pick_count > 0:
                    genre_score += pick_count / total_genre_picks
            
            if genre_score > 0:
                boost = 0.3 * min(genre_score, 1.0)
                movie.group_score += boost
        
        return recommendations
    
    def get_group_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary of the group's preferences"""
        
        if self.preferences['total_sessions'] == 0:
            return {
                'message': "This is your first movie night together!",
                'sessions': 0
            }
        
        # Top genres
        top_genres = sorted(
            self.preferences['preferred_genres'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Top cinemas
        top_cinemas = sorted(
            self.preferences['preferred_cinemas'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:2]
        
        # Most satisfied user
        if self.preferences['user_satisfaction']:
            most_satisfied = max(
                self.preferences['user_satisfaction'].items(),
                key=lambda x: x[1]
            )[0]
        else:
            most_satisfied = None
        
        return {
            'sessions': self.preferences['total_sessions'],
            'top_genres': [int(g[0]) for g in top_genres],
            'top_cinemas': [c[0] for c in top_cinemas],
            'most_satisfied_user': most_satisfied,
            'message': f"You've had {self.preferences['total_sessions']} movie nights together!"
        }


def create_group_id(usernames: List[str]) -> str:
    """
    Create a consistent group ID from usernames
    
    Args:
        usernames: List of Letterboxd usernames
    
    Returns:
        Consistent group identifier (sorted, joined)
    """
    return "_".join(sorted([u.strip().lower() for u in usernames]))


# Genre ID to name mapping (TMDb genre IDs)
GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}