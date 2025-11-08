"""
mood_filter.py

Filter and boost movie recommendations based on group mood.
Enables natural conversation: "We're feeling excited tonight!"
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


# Map moods to TMDb genre IDs
MOOD_GENRES = {
    'happy': {
        'primary': [35, 10402, 16],  # Comedy, Music, Animation
        'secondary': [10751, 10749],  # Family, Romance
        'description': "Uplifting, fun, and feel-good"
    },
    'sad': {
        'primary': [18, 10749],  # Drama, Romance
        'secondary': [36, 10402],  # History, Music
        'description': "Emotional, moving, and cathartic"
    },
    'excited': {
        'primary': [28, 12, 878],  # Action, Adventure, Sci-Fi
        'secondary': [14, 53],  # Fantasy, Thriller
        'description': "Thrilling, fast-paced, and energetic"
    },
    'thoughtful': {
        'primary': [18, 99, 36],  # Drama, Documentary, History
        'secondary': [9648, 878],  # Mystery, Sci-Fi
        'description': "Deep, intellectual, and contemplative"
    },
    'scared': {
        'primary': [27, 53],  # Horror, Thriller
        'secondary': [9648, 878],  # Mystery, Sci-Fi
        'description': "Scary, suspenseful, and intense"
    },
    'relaxed': {
        'primary': [35, 10749, 10402],  # Comedy, Romance, Music
        'secondary': [16, 10751],  # Animation, Family
        'description': "Easy-going, comfortable, and pleasant"
    },
    'adventurous': {
        'primary': [12, 14, 878],  # Adventure, Fantasy, Sci-Fi
        'secondary': [28, 16],  # Action, Animation
        'description': "Epic, imaginative, and escapist"
    },
    'romantic': {
        'primary': [10749, 35],  # Romance, Comedy
        'secondary': [18, 10402],  # Drama, Music
        'description': "Heartwarming, sweet, and charming"
    },
    'nostalgic': {
        'primary': [18, 36, 10751],  # Drama, History, Family
        'secondary': [10402, 16],  # Music, Animation
        'description': "Classic, timeless, and sentimental"
    },
    'energetic': {
        'primary': [28, 12, 35],  # Action, Adventure, Comedy
        'secondary': [10402, 878],  # Music, Sci-Fi
        'description': "Dynamic, lively, and stimulating"
    }
}


# Mood aliases (for natural language)
MOOD_ALIASES = {
    # Happy variations
    'cheerful': 'happy',
    'joyful': 'happy',
    'upbeat': 'happy',
    'positive': 'happy',
    
    # Sad variations
    'melancholy': 'sad',
    'emotional': 'sad',
    'tearjerker': 'sad',
    'crying': 'sad',
    
    # Excited variations
    'pumped': 'excited',
    'hyped': 'excited',
    'thrilled': 'excited',
    'intense': 'excited',
    
    # Thoughtful variations
    'contemplative': 'thoughtful',
    'philosophical': 'thoughtful',
    'deep': 'thoughtful',
    'intellectual': 'thoughtful',
    
    # Scared variations
    'scary': 'scared',
    'horror': 'scared',
    'terrifying': 'scared',
    'spooky': 'scared',
    
    # Relaxed variations
    'chill': 'relaxed',
    'calm': 'relaxed',
    'easy': 'relaxed',
    'lazy': 'relaxed',
    
    # Adventurous variations
    'epic': 'adventurous',
    'fantasy': 'adventurous',
    'exploring': 'adventurous',
    
    # Romantic variations
    'love': 'romantic',
    'date': 'romantic',
    'sweet': 'romantic',
    
    # Nostalgic variations
    'classic': 'nostalgic',
    'retro': 'nostalgic',
    'old': 'nostalgic',
    
    # Energetic variations
    'active': 'energetic',
    'fun': 'energetic',
    'wild': 'energetic'
}


@dataclass
class MoodMatch:
    """Represents how well a movie matches a mood"""
    mood: str
    match_score: float  # 0.0 - 1.0
    matching_genres: List[str]
    boost_applied: float


class MoodFilter:
    """
    Filter and boost recommendations based on group mood
    
    Usage:
        filter = MoodFilter()
        adjusted_movies = filter.apply_mood(movies, mood="excited")
    """
    
    def __init__(self):
        self.genre_id_to_name = {
            28: "Action", 12: "Adventure", 16: "Animation",
            35: "Comedy", 80: "Crime", 99: "Documentary",
            18: "Drama", 10751: "Family", 14: "Fantasy",
            36: "History", 27: "Horror", 10402: "Music",
            9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
            53: "Thriller", 10752: "War", 37: "Western"
        }
    
    def normalize_mood(self, mood_input: str) -> Optional[str]:
        """
        Normalize mood input to standard mood
        
        Args:
            mood_input: User's mood input (e.g., "chill", "pumped", "happy")
        
        Returns:
            Normalized mood or None if unrecognized
        """
        mood_lower = mood_input.strip().lower()
        
        # Direct match
        if mood_lower in MOOD_GENRES:
            return mood_lower
        
        # Check aliases
        if mood_lower in MOOD_ALIASES:
            return MOOD_ALIASES[mood_lower]
        
        return None
    
    def get_available_moods(self) -> List[Dict[str, str]]:
        """
        Get list of all available moods with descriptions
        
        Returns:
            List of {mood, description} dicts
        """
        return [
            {
                'mood': mood,
                'description': config['description']
            }
            for mood, config in MOOD_GENRES.items()
        ]
    
    def calculate_mood_match(
        self,
        movie: Any,  # GroupMatchedMovie
        mood: str
    ) -> MoodMatch:
        """
        Calculate how well a movie matches the mood
        
        Args:
            movie: GroupMatchedMovie object
            mood: Normalized mood string
        
        Returns:
            MoodMatch object with score and details
        """
        if not movie.tmdb or mood not in MOOD_GENRES:
            return MoodMatch(
                mood=mood,
                match_score=0.0,
                matching_genres=[],
                boost_applied=0.0
            )
        
        mood_config = MOOD_GENRES[mood]
        movie_genre_ids = set(movie.tmdb.get('genre_ids', []))
        
        # Calculate match scores
        primary_genres = set(mood_config['primary'])
        secondary_genres = set(mood_config['secondary'])
        
        primary_matches = movie_genre_ids & primary_genres
        secondary_matches = movie_genre_ids & secondary_genres
        
        # Score calculation
        primary_score = len(primary_matches) / max(len(primary_genres), 1)
        secondary_score = len(secondary_matches) / max(len(secondary_genres), 1)
        
        match_score = (primary_score * 0.7) + (secondary_score * 0.3)
        
        # Get matching genre names
        matching_genre_names = [
            self.genre_id_to_name.get(gid, f"Genre {gid}")
            for gid in (primary_matches | secondary_matches)
        ]
        
        # Calculate boost amount
        if match_score > 0.7:
            boost = 0.6
        elif match_score > 0.4:
            boost = 0.4
        elif match_score > 0.2:
            boost = 0.2
        else:
            boost = 0.0
        
        return MoodMatch(
            mood=mood,
            match_score=match_score,
            matching_genres=matching_genre_names,
            boost_applied=boost
        )
    
    def apply_mood(
        self,
        recommendations: List[Any],  # List[GroupMatchedMovie]
        mood: str,
        aggressive: bool = False
    ) -> List[Any]:
        """
        Filter and boost recommendations based on mood
        
        Args:
            recommendations: List of GroupMatchedMovie objects
            mood: Mood string (will be normalized)
            aggressive: If True, remove movies that don't match at all
        
        Returns:
            Adjusted list of recommendations
        """
        
        # Normalize mood
        normalized_mood = self.normalize_mood(mood)
        
        if not normalized_mood:
            print(f" Unrecognized mood: '{mood}'")
            print(f"   Available moods: {', '.join(MOOD_GENRES.keys())}")
            return recommendations
        
        print(f"\n Applying mood filter: '{normalized_mood}'")
        print(f"   {MOOD_GENRES[normalized_mood]['description']}")
        
        # Calculate mood match for each movie
        adjusted_movies = []
        
        for movie in recommendations:
            mood_match = self.calculate_mood_match(movie, normalized_mood)
            
            # Store mood info on movie object
            movie.mood_match = mood_match
            
            # Apply boost
            original_score = movie.group_score
            movie.group_score += mood_match.boost_applied
            
            # Filter out non-matches if aggressive mode
            if aggressive and mood_match.match_score < 0.1:
                continue
            
            adjusted_movies.append(movie)
            
            # Log significant boosts
            if mood_match.boost_applied > 0.3:
                print(f"      Boosted '{movie.title}' by {mood_match.boost_applied:.2f}")
                print(f"      Matches: {', '.join(mood_match.matching_genres)}")
        
        # Sort by new scores
        adjusted_movies.sort(key=lambda m: m.group_score, reverse=True)
        
        print(f" Mood filter applied! {len(adjusted_movies)} movies match the vibe\n")
        
        return adjusted_movies
    
    def get_mood_explanation(self, movie: Any, mood: str) -> str:
        """
        Generate human-readable explanation of mood match
        
        Args:
            movie: GroupMatchedMovie with mood_match attribute
            mood: The mood that was applied
        
        Returns:
            Explanation string
        """
        if not hasattr(movie, 'mood_match'):
            return ""
        
        mood_match = movie.mood_match
        
        if mood_match.match_score > 0.7:
            quality = "Perfect"
            emoji = ":D"
        elif mood_match.match_score > 0.4:
            quality = "Great"
            emoji = ":))"
        elif mood_match.match_score > 0.2:
            quality = "Good"
            emoji = ":)"
        else:
            return ""
        
        if mood_match.matching_genres:
            genres_str = " + ".join(mood_match.matching_genres[:2])
            return f"{emoji} {quality} for {mood}: {genres_str}"
        
        return f"{emoji} {quality} match for {mood} mood"