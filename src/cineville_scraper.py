"""
Cineville Scraper - Get real movie showtimes from Cineville Amsterdam
Uses Next.js __NEXT_DATA__ JSON for reliable scraping
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re


class CinevilleScraper:
    def __init__(self):
        self.base_url = "https://www.cineville.nl"
        # Try different URLs - they might have different data
        self.possible_urls = [
            f"{self.base_url}/nl-NL/filmagenda",
            f"{self.base_url}/nl-NL/amsterdam", 
            f"{self.base_url}/nl/filmagenda",
            f"{self.base_url}/nl/amsterdam",
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
        })
        
        # Known Cineville cinemas in Amsterdam
        self.known_cinemas = {
            'eye': 'EYE Filmmuseum',
            'rialto': 'Rialto',
            'kriterion': 'Kriterion',
            'ketelhuis': 'Het Ketelhuis',
            'filmhallen': 'The Movies',
            'lab111': 'LAB111',
            'de uitkijk': 'De Uitkijk',
            'studio/k': 'Studio/K',
        }
    
    def get_page_html(self, url):
        """Fetch HTML content"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            print(f"Status: {response.status_code}")
            return response.text
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def extract_nextjs_data(self, html_content):
        """
        Extract Next.js data from __NEXT_DATA__ script tag
        This is where all the page data is stored!
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the __NEXT_DATA__ script tag
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
        
        if not next_data_script:
            print("Could not find __NEXT_DATA__ script tag")
            return None
        
        try:
            # Parse the JSON content
            data = json.loads(next_data_script.string)
            print("Successfully extracted Next.js data!")
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None
    
    def parse_showtimes_from_nextjs_data(self, data):
        """
        Parse showtimes from Next.js data structure
        
        The structure varies, so we'll search recursively
        """
        showtimes = []
        
        print("\n Searching Next.js data for showtimes...")
        
        # Helper function to recursively search for movie data
        def search_for_movies(obj, path=""):
            results = []
            
            if isinstance(obj, dict):
                # Check if this looks like a movie/showtime object
                if self._looks_like_movie(obj):
                    movie_data = self._extract_movie_from_object(obj)
                    if movie_data:
                        results.append(movie_data)
                        print(f"   Found: {movie_data['title']}")
                
                # Recursively search nested objects
                for key, value in obj.items():
                    results.extend(search_for_movies(value, f"{path}.{key}"))
            
            elif isinstance(obj, list):
                # Search through array items
                for i, item in enumerate(obj):
                    results.extend(search_for_movies(item, f"{path}[{i}]"))
            
            return results
        
        showtimes = search_for_movies(data)
        return showtimes
    
    def _looks_like_movie(self, obj):
        """
        Check if an object looks like a movie/showtime entry
        """
        if not isinstance(obj, dict):
            return False
        
        # Common keys that indicate movie data
        movie_indicators = ['title', 'film', 'movie', 'name']
        time_indicators = ['time', 'start', 'showtime', 'datetime', 'date']
        cinema_indicators = ['cinema', 'theater', 'venue', 'location']
        
        has_title = any(key.lower() in str(obj.keys()).lower() for key in movie_indicators)
        has_time_or_cinema = any(key.lower() in str(obj.keys()).lower() for key in time_indicators + cinema_indicators)
        
        return has_title and has_time_or_cinema
    
    def _extract_movie_from_object(self, obj):
        """
        Extract movie information from a data object
        """
        movie_data = {
            'title': None,
            'cinema': None,
            'showtime': None,
            'source': 'cineville'
        }
        
        # Extract title (try various keys)
        for key in ['title', 'name', 'film', 'movie', 'filmTitle']:
            if key in obj:
                movie_data['title'] = str(obj[key])
                break
        
        if not movie_data['title']:
            return None
        
        # Extract cinema
        for key in ['cinema', 'theater', 'venue', 'location', 'cinemaName', 'theaterName']:
            if key in obj:
                cinema_name = str(obj[key])
                # Try to match with known cinemas
                for known_key, known_name in self.known_cinemas.items():
                    if known_key in cinema_name.lower():
                        movie_data['cinema'] = known_name
                        break
                if not movie_data['cinema']:
                    movie_data['cinema'] = cinema_name
                break
        
        if not movie_data['cinema']:
            movie_data['cinema'] = "Cinema TBD"
        
        # Extract showtime
        for key in ['time', 'start', 'startTime', 'showtime', 'datetime', 'date', 'startDateTime']:
            if key in obj:
                time_value = obj[key]
                movie_data['showtime'] = self._parse_time_value(time_value)
                if movie_data['showtime']:
                    break
        
        return movie_data if movie_data['showtime'] else None
    
    def _parse_time_value(self, time_value):
        """Parse various time formats"""
        if not time_value:
            return None
        
        try:
            # Try ISO format
            if isinstance(time_value, str):
                # ISO 8601 format
                if 'T' in time_value or '+' in time_value or 'Z' in time_value:
                    return datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                
                # Time only (HH:MM)
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_value)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    today = datetime.now()
                    return today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            pass
        
        return None
    
    def get_showtimes_today(self):
        """
        Get all showtimes for today from Cineville
        """
        print("\n" + "="*60)
        print("CINEVILLE SCRAPER (Next.js Data Extraction)")
        print("="*60)
        
        # Try different URLs
        for url in self.possible_urls:
            print(f"\n Trying: {url}")
            
            html = self.get_page_html(url)
            if not html:
                continue
            
            # Extract Next.js data
            nextjs_data = self.extract_nextjs_data(html)
            if not nextjs_data:
                continue
            
            # Parse showtimes
            showtimes = self.parse_showtimes_from_nextjs_data(nextjs_data)
            
            if showtimes:
                print(f"\n Successfully scraped {len(showtimes)} showtimes!")
                return showtimes
        
        # If all URLs failed, use mock data
        print("\n Could not scrape any data from Cineville")
        print(" Using mock data instead...")
        return self._get_mock_data()
    
    def filter_evening_showtimes(self, showtimes, start_hour=18, end_hour=23):
        """Filter for evening showtimes (18:00-23:00)"""
        evening_shows = []
        
        for show in showtimes:
            if show['showtime'] and isinstance(show['showtime'], datetime):
                hour = show['showtime'].hour
                if start_hour <= hour < end_hour:
                    evening_shows.append(show)
        
        return evening_shows
    
    def get_movies_for_free_slot(self, free_start, free_end):
        """
        Get movies that fit in a free time slot
        """
        all_showtimes = self.get_showtimes_today()
        
        matching = []
        for show in all_showtimes:
            if show['showtime'] and isinstance(show['showtime'], datetime):
                # Movie should start within free slot
                # Assume 2.5 hour movie + 30 min buffer = 3 hours total
                movie_end = show['showtime'] + timedelta(hours=3)
                
                if free_start <= show['showtime'] <= free_end:
                    # Check if movie ends before free time ends (with buffer)
                    if movie_end <= free_end + timedelta(hours=0.5):
                        matching.append(show)
        
        print(f"\n Found {len(matching)} movies in your free slot")
        return matching
    
    def _get_mock_data(self):
        """
        Fallback mock data when scraping fails
        """
        now = datetime.now()
        base_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
        
        mock_movies = [
            {
                'title': 'Perfect Days',
                'cinema': 'EYE Filmmuseum',
                'showtime': base_time.replace(hour=19, minute=30),
                'source': 'mock'
            },
            {
                'title': 'The Zone of Interest',
                'cinema': 'Rialto',
                'showtime': base_time.replace(hour=20, minute=15),
                'source': 'mock'
            },
            {
                'title': 'Past Lives',
                'cinema': 'Kriterion',
                'showtime': base_time.replace(hour=20, minute=45),
                'source': 'mock'
            },
            {
                'title': 'Anatomy of a Fall',
                'cinema': 'The Movies',
                'showtime': base_time.replace(hour=21, minute=0),
                'source': 'mock'
            },
            {
                'title': 'Poor Things',
                'cinema': 'LAB111',
                'showtime': base_time.replace(hour=21, minute=30),
                'source': 'mock'
            },
            {
                'title': 'All of Us Strangers',
                'cinema': 'De Uitkijk',
                'showtime': base_time.replace(hour=20, minute=0),
                'source': 'mock'
            }
        ]
        
        print(f"Loaded {len(mock_movies)} mock movies")
        return mock_movies
    
    def save_nextjs_data(self, filename='data/cineville_nextjs_data.json'):
        """
        Save the Next.js data to a file for inspection
        Useful for debugging
        """
        for url in self.possible_urls:
            html = self.get_page_html(url)
            if html:
                nextjs_data = self.extract_nextjs_data(html)
                if nextjs_data:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(nextjs_data, f, indent=2, ensure_ascii=False)
                    print(f"Saved Next.js data to {filename}")
                    print(f"Open it to inspect the data structure")
                    return True
        
        return False


def test_cineville_scraper():
    """Test the Cineville scraper"""
    scraper = CinevilleScraper()
    
    print("\n" + "="*60)
    print(" TESTING CINEVILLE SCRAPER")
    print("="*60)
    
    # Test 1: Save Next.js data for inspection
    print("\n Test 1: Extracting Next.js data...")
    scraper.save_nextjs_data()
    
    # Test 2: Get all showtimes
    print("\n Test 2: Getting today's showtimes...")
    showtimes = scraper.get_showtimes_today()
    
    if showtimes:
        print(f"\n Found {len(showtimes)} total showtimes:")
        for i, show in enumerate(showtimes[:10], 1):
            time_str = show['showtime'].strftime('%H:%M') if show['showtime'] else 'TBD'
            source = "web" if show['source'] == 'cineville' else "box"
            print(f"   {source} {i}. {show['title']}")
            print(f"      {show['cinema']}")
            print(f"      {time_str}")
    
    # Test 3: Filter evening showtimes
    print("\n Test 3: Filtering evening showtimes (18:00-23:00)...")
    evening = scraper.filter_evening_showtimes(showtimes)
    
    print(f"\n Found {len(evening)} evening showtimes:")
    for show in evening[:5]:
        time_str = show['showtime'].strftime('%H:%M') if show['showtime'] else 'TBD'
        print(f"   • {time_str} - {show['title']} @ {show['cinema']}")
    
    # Test 4: Get movies for a free slot
    print("\nTest 4: Finding movies for free slot (19:00-23:00)...")
    free_start = datetime.now().replace(hour=19, minute=0)
    free_end = datetime.now().replace(hour=23, minute=0)
    
    matching = scraper.get_movies_for_free_slot(free_start, free_end)
    
    if matching:
        print(f"\n {len(matching)} movies fit in your free slot:")
        for show in matching:
            time_str = show['showtime'].strftime('%H:%M')
            print(f"   • {time_str} - {show['title']} @ {show['cinema']}")
    else:
        print("\n No movies found in free slot")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    return scraper, showtimes


if __name__ == "__main__":
    test_cineville_scraper()