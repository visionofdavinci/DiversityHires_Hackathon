import { MovieRecommendation, CalendarSlot, UserProfile } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export const api = {
  // Calendar Integration
  async getCalendarAuth(username: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/calendar/auth/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username })
    });
    const data = await response.json();
    return data.auth_url;
  },

  async getCalendarFreeSlots(username: string, daysAhead: number = 7): Promise<CalendarSlot[]> {
    const response = await fetch(
      `${API_BASE_URL}/calendar/${username}/events?days_ahead=${daysAhead}`
    );
    if (!response.ok) {
      throw new Error('Failed to fetch calendar events');
    }
    const data = await response.json();
    // Convert events to free slots format if needed
    return data.events || [];
  },

  // Letterboxd Integration
  async getUserProfile(username: string, quick: boolean = true): Promise<UserProfile> {
    const queryParam = quick ? '?quick=true' : '';
    const response = await fetch(`${API_BASE_URL}/letterboxd/${username}${queryParam}`);
    if (!response.ok) {
      throw new Error('Failed to fetch user profile');
    }
    const data = await response.json();
    
    // Transform the response to match UserProfile type
    return {
      username: data.letterboxd_username || username,
      ratings: (data.recent_movies || []).map((movie: any) => ({
        movieTitle: movie.title,
        rating: movie.rating || 0,
        year: movie.year
      }))
    };
  },

  async getUserRatings(username: string): Promise<UserProfile['ratings']> {
    const profile = await this.getUserProfile(username);
    return profile.ratings;
  },

  // Cineville Integration  
  async getMovieRecommendations(
    usernames: string[],
    options: {
      daysAhead?: number;
      limitAmsterdam?: boolean;
      maxResults?: number;
      useCalendar?: boolean;
      minSlotMinutes?: number;
      mood?: string;
    } = {}
  ): Promise<MovieRecommendation[]> {
    const response = await fetch(`${API_BASE_URL}/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        usernames,
        days_ahead: options.daysAhead || 7,
        limit_amsterdam: options.limitAmsterdam !== false,
        max_results: options.maxResults || 10,
        use_calendar: options.useCalendar !== false,
        min_hours: options.minSlotMinutes ? options.minSlotMinutes / 60 : 2,
        mood: options.mood
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch recommendations');
    }
    
    const data = await response.json();
    return data.recommendations || [];
  },

  async getCinevilleMovies(options: {
    limitAmsterdam?: boolean;
    daysAhead?: number;
  } = {}): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/cineville/upcoming`);
    if (!response.ok) {
      throw new Error('Failed to fetch Cineville movies');
    }
    return response.json();
  }
};