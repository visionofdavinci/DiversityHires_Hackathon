"""
poll_manager.py

Handles creation and management of group movie polls with multi-vote support.
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


class PollManager:
    """Manages movie polls with option-based multi-voting."""
    
    def __init__(self):
        self.polls: Dict[str, dict] = {}
    
    def create_poll(
        self, 
        title: str, 
        options: List[dict], 
        participants: List[str],
        max_votes_per_user: int = 1
    ) -> str:
        """
        Create a new poll.
        
        Args:
            title: Poll title
            options: List of dicts with 'text', 'movie', 'cinema', 'time'
            participants: List of usernames who can vote
            max_votes_per_user: Maximum votes each user can cast
            
        Returns:
            poll_id: Unique identifier for the poll
        """
        poll_id = str(uuid.uuid4())
        
        self.polls[poll_id] = {
            'poll_id': poll_id,
            'title': title,
            'options': options,
            'participants': participants,
            'max_votes_per_user': max_votes_per_user,
            'votes': {},  # {username: [option_indices]}
            'created_at': datetime.utcnow().isoformat()
        }
        
        return poll_id
    
    def submit_vote(
        self, 
        poll_id: str, 
        username: str, 
        option_indices: List[int]
    ) -> bool:
        """
        Submit a vote for a poll.
        
        Args:
            poll_id: Poll identifier
            username: Voter username
            option_indices: List of option indices (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return False
        
        if username not in poll['participants']:
            return False
        
        if len(option_indices) > poll['max_votes_per_user']:
            return False
        
        # Validate indices
        if any(i < 0 or i >= len(poll['options']) for i in option_indices):
            return False
        
        poll['votes'][username] = option_indices
        return True
    
    def get_poll_results(self, poll_id: str) -> Optional[dict]:
        """
        Get poll results with vote tallies.
        
        Returns:
            Dict with votes, option_tallies, movie_tallies
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return None
        
        # Tally votes by option
        option_tallies = {}
        for i in range(len(poll['options'])):
            option_id = f"option_{i}"
            option_tallies[option_id] = 0
        
        for username, indices in poll['votes'].items():
            for idx in indices:
                option_id = f"option_{idx}"
                option_tallies[option_id] += 1
        
        # Tally votes by movie
        movie_tallies = {}
        for username, indices in poll['votes'].items():
            for idx in indices:
                movie = poll['options'][idx].get('movie', 'Unknown')
                movie_tallies[movie] = movie_tallies.get(movie, 0) + 1
        
        return {
            'poll_id': poll_id,
            'votes': poll['votes'],
            'option_tallies': option_tallies,
            'movie_tallies': movie_tallies,
            'total_votes': len(poll['votes']),
            'total_participants': len(poll['participants'])
        }