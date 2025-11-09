from flask import Flask, jsonify, request
from flask_cors import CORS
from letterboxd_integration import LetterboxdIntegration
from cineville_scraper import CinevilleScraper
from calendar_agent import authenticate, get_events_for_user
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize services
cineville_scraper = CinevilleScraper()

@app.route('/api/letterboxd/ratings', methods=['GET'])
def get_letterboxd_ratings():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Get user's movie ratings from Letterboxd
        lb_client = LetterboxdIntegration(username=username)
        preferences = lb_client.get_preferences()
        
        formatted_ratings = [{
            'title': pref.title,
            'rating': pref.rating if pref.rating else 0,
            'year': pref.year
        } for pref in preferences if pref.rating]
        
        return jsonify({'ratings': formatted_ratings, 'username': username})
    except Exception as e:
        print(f"Error fetching Letterboxd ratings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cineville/movies', methods=['GET'])
def get_cineville_movies():
    try:
        # Get upcoming movies from Cineville for the next week
        movies = cineville_scraper.get_all_showtimes(days_ahead=7, limit_amsterdam=True)
        
        formatted_movies = [{
            'title': movie['title'],
            'location': movie.get('cinema_name', 'Amsterdam'),
            'theater': movie.get('cinema_name', ''),
            'showtime': movie.get('start_time', '')
        } for movie in movies]
        
        return jsonify(formatted_movies)
    except Exception as e:
        print(f"Error fetching Cineville movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar/auth', methods=['POST'])
def authenticate_calendar():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Extract username from email (e.g., user@gmail.com -> user)
        username = email.split('@')[0]
        token_filename = f"{username}.json"
        
        # Authenticate and get calendar service
        service = authenticate(token_filename=token_filename)
        
        # Get events for the next 2 weeks
        events = get_events_for_user(service, username)
        
        formatted_events = [{
            'title': event.get('summary', 'Untitled Event'),
            'start': event.get('start', {}).get('dateTime', ''),
            'end': event.get('end', {}).get('dateTime', '')
        } for event in events]
        
        return jsonify({
            'events': formatted_events,
            'username': username
        })
    except Exception as e:
        print(f"Error authenticating calendar: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000, debug=True)