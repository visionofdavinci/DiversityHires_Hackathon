"""
Test the new group learning and mood features
"""

import os
from movie_matcher import GroupMovieMatcher, TMDbClient
from cineville_scraper import CinevilleScraper
from group_history import GENRE_MAP, create_group_id
from mood_filter import MoodFilter


def test_mood_filter():
    """Test mood-based filtering"""
    print("\n" + "="*60)
    print("TEST 1: MOOD-BASED FILTERING")
    print("="*60)
    
    # Set up
    usernames = os.getenv("LETTERBOXD_USERNAMES", "visionofdavinci").split(",")
    
    cineville = CinevilleScraper()
    tmdb = TMDbClient()
    matcher = GroupMovieMatcher(cineville, tmdb)
    
    # Test different moods
    moods_to_test = ['excited', 'relaxed', 'thoughtful']
    
    for mood in moods_to_test:
        print(f"\n--- Testing mood: {mood} ---")
        
        results, group_history = matcher.match_group(
            usernames=usernames,
            days_ahead=3,
            max_results=5,
            mood=mood,
            learn_from_history=False  # Disable for pure mood testing
        )
        
        print(f"\nTop 3 {mood} recommendations:")
        for i, movie in enumerate(results[:3], 1):
            mood_exp = MoodFilter().get_mood_explanation(movie, mood)
            print(f"{i}. {movie.title} - Score: {movie.group_score:.2f}")
            if mood_exp:
                print(f"   {mood_exp}")


def test_group_learning():
    """Test group learning over time"""
    print("\n" + "="*60)
    print(" TEST 2: GROUP LEARNING")
    print("="*60)
    
    usernames = os.getenv("LETTERBOXD_USERNAMES", "visionofdavinci").split(",")
    
    cineville = CinevilleScraper()
    tmdb = TMDbClient()
    matcher = GroupMovieMatcher(cineville, tmdb)
    
    # First recommendation (no history)
    print("\n--- First Time (No History) ---")
    results1, group_history = matcher.match_group(
        usernames=usernames,
        days_ahead=3,
        max_results=10,
        learn_from_history=True
    )
    
    print(f"\nTop 3 recommendations:")
    for i, movie in enumerate(results1[:3], 1):
        print(f"{i}. {movie.title} - Score: {movie.group_score:.2f}")
    
    # Simulate choosing a movie
    print("\n--- Simulating Group Choice ---")
    chosen = results1[1]  # Choose second movie
    print(f"Group chose: {chosen.title}")
    
    group_history.record_choice(
        group_members=usernames,
        all_recommendations=results1,
        chosen_movie=chosen
    )
    
    # Second recommendation (with history)
    print("\n--- Second Time (With History) ---")
    results2, group_history = matcher.match_group(
        usernames=usernames,
        days_ahead=3,
        max_results=10,
        learn_from_history=True
    )
    
    print(f"\nTop 3 recommendations (adjusted by learning):")
    for i, movie in enumerate(results2[:3], 1):
        boost_reasons = getattr(movie, 'boost_reasons', [])
        boost_str = f" [{', '.join(boost_reasons)}]" if boost_reasons else ""
        print(f"{i}. {movie.title} - Score: {movie.group_score:.2f}{boost_str}")
    
    # Show what was learned
    print("\n--- Group Preferences Learned ---")
    if group_history.preferences['preferred_genres']:
        print("Top genres:", [
            GENRE_MAP.get(int(gid), gid)
            for gid in list(group_history.preferences['preferred_genres'].keys())[:3]
        ])


def test_combined():
    """Test mood + learning together"""
    print("\n" + "="*60)
    print(" TEST 3: MOOD + LEARNING COMBINED")
    print("="*60)
    
    usernames = os.getenv("LETTERBOXD_USERNAMES", "visionofdavinci").split(",")
    
    cineville = CinevilleScraper()
    tmdb = TMDbClient()
    matcher = GroupMovieMatcher(cineville, tmdb)
    
    # Get recommendations with both features
    results, group_history = matcher.match_group(
        usernames=usernames,
        days_ahead=3,
        max_results=10,
        mood='excited',
        learn_from_history=True
    )
    
    print(f"\nTop 5 with BOTH mood ('excited') and learning:")
    for i, movie in enumerate(results[:5], 1):
        mood_exp = MoodFilter().get_mood_explanation(movie, 'excited')
        boost_reasons = getattr(movie, 'boost_reasons', [])
        
        print(f"\n{i}. {movie.title} ({movie.year}) - {movie.group_score:.2f}")
        if mood_exp:
            print(f"   {mood_exp}")
        if boost_reasons:
            print(f"   Learning: {', '.join(boost_reasons)}")


if __name__ == "__main__":
    # Run all tests
    test_mood_filter()
    test_group_learning()
    test_combined()
    
    print("\n" + "="*60)
    print(" ALL TESTS COMPLETE!")
    print("="*60)