import { MovieRecommendation, CalendarSlot, UserProfile } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  // Calendar Integration
  async getCalendarAuth(username: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/auth/calendar/${username}`);
    const data = await response.json();
    return data.authUrl;
  },

  async getCalendarFreeSlots(username: string, daysAhead: number = 7): Promise<CalendarSlot[]> {
    const response = await fetch(
      `${API_BASE_URL}/calendar/${username}/free-slots?days=${daysAhead}`
    );
    return response.json();
  },

  // Letterboxd Integration
  async getUserProfile(username: string): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/letterboxd/${username}/profile`);
    return response.json();
  },

  async getUserRatings(username: string): Promise<UserProfile['ratings']> {
    const response = await fetch(`${API_BASE_URL}/letterboxd/${username}/ratings`);
    return response.json();
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
    // Convert options to string values for URLSearchParams
    const queryParams: Record<string, string> = {
      usernames: usernames.join(','),
      ...(options.daysAhead !== undefined && { daysAhead: options.daysAhead.toString() }),
      ...(options.limitAmsterdam !== undefined && { limitAmsterdam: options.limitAmsterdam.toString() }),
      ...(options.maxResults !== undefined && { maxResults: options.maxResults.toString() }),
      ...(options.useCalendar !== undefined && { useCalendar: options.useCalendar.toString() }),
      ...(options.minSlotMinutes !== undefined && { minSlotMinutes: options.minSlotMinutes.toString() }),
      ...(options.mood && { mood: options.mood })
    };

    const params = new URLSearchParams(queryParams);
    
    const response = await fetch(`${API_BASE_URL}/recommendations?${params}`);
    return response.json();
  },

  async getCinevilleMovies(options: {
    limitAmsterdam?: boolean;
    daysAhead?: number;
  } = {}): Promise<any[]> {
    const params = new URLSearchParams(options as any);
    const response = await fetch(`${API_BASE_URL}/cineville/movies?${params}`);
    return response.json();
  }
};