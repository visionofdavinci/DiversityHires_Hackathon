from flask import Flask, jsonify
from flask_cors import CORS
from letterboxd_integration import LetterboxdClient
from cineville_scraper import CinevilleScraper
from calendar_agent import CalendarAgent
from utils.config_loader import ConfigLoader
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize services
config = ConfigLoader()
letterboxd_client = LetterboxdClient()
cineville_scraper = CinevilleScraper()
calendar_agent = CalendarAgent()

@app.route('/api/letterboxd', methods=['GET'])
def get_letterboxd_data():
    try:
        # Get user's watched films from Letterboxd
        watched_films = letterboxd_client.get_watched_films()
        formatted_films = [{
            'title': film['title'],
            'rating': film.get('rating', None),
            'watchedDate': film.get('watched_date', None),
            'review': film.get('review', '')
        } for film in watched_films]
        return jsonify(formatted_films)
    except Exception as e:
        print(f"Error fetching Letterboxd data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cineville', methods=['GET'])
def get_cineville_data():
    try:
        # Get upcoming movies from Cineville
        movies = cineville_scraper.get_upcoming_movies()
        formatted_movies = [{
            'title': movie['title'],
            'location': movie.get('location', 'Amsterdam'),
            'theater': movie.get('theater', ''),
            'showtime': movie.get('showtime', '')
        } for movie in movies]
        return jsonify(formatted_movies)
    except Exception as e:
        print(f"Error fetching Cineville data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar_data():
    try:
        # Get calendar events
        events = calendar_agent.get_events()
        formatted_events = [{
            'id': str(event.get('id', '')),
            'title': event.get('summary', 'Untitled Event'),
            'start': event.get('start', {}).get('dateTime', ''),
            'end': event.get('end', {}).get('dateTime', ''),
            'description': event.get('description', '')
        } for event in events]
        return jsonify(formatted_events)
    except Exception as e:
        print(f"Error fetching calendar data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)