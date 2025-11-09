export interface ShowTime {
  cinema: string;
  start: string; // ISO datetime string
}

export interface MovieRecommendation {
  title: string;
  year?: number;
  group_score: number;
  per_user_scores: Record<string, number>;
  showtimes: ShowTime[];
  cineville: any; // Full Cineville movie data
  tmdb?: any; // Optional TMDb data
}

export interface UserProfile {
  username: string;
  ratings: Array<{
    movieTitle: string;
    rating: number;
    year?: number;
  }>;
}

export interface CalendarSlot {
  start: string; // ISO datetime string
  end: string; // ISO datetime string
}

export interface MovieMatch {
  recommendation: MovieRecommendation;
  availableSlots: CalendarSlot[];
}