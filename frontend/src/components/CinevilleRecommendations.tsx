import { useState, useEffect } from 'react';
import { MovieRecommendation } from '@/types';
import { api } from '@/services/api';

interface CinevilleRecommendationsProps {
  usernames: string[];
  options?: {
    daysAhead?: number;
    limitAmsterdam?: boolean;
    maxResults?: number;
    useCalendar?: boolean;
    minSlotMinutes?: number;
    mood?: string;
  };
}

export default function CinevilleRecommendations({
  usernames,
  options = {}
}: CinevilleRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<MovieRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await api.getMovieRecommendations(usernames, options);
        setRecommendations(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load recommendations');
      } finally {
        setIsLoading(false);
      }
    };

    if (usernames.length > 0) {
      loadRecommendations();
    }
  }, [usernames, options]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Movie Recommendations</h2>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {recommendations.map((movie, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
          >
            {movie.tmdb?.backdrop_path && (
              <div className="aspect-video bg-gray-200">
                <img
                  src={`https://image.tmdb.org/t/p/w500${movie.tmdb.backdrop_path}`}
                  alt={movie.title}
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            
            <div className="p-4 space-y-4">
              <div>
                <h3 className="text-lg font-semibold">
                  {movie.title}
                  {movie.year && <span className="text-gray-500"> ({movie.year})</span>}
                </h3>
                <p className="text-gray-600">
                  Group Score: {(movie.group_score * 5).toFixed(1)} / 10
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Individual Scores:</h4>
                {Object.entries(movie.per_user_scores).map(([username, score]) => (
                  <div key={username} className="flex justify-between items-center">
                    <span className="text-sm">{username}</span>
                    <span className="text-sm font-medium">
                      {(score * 5).toFixed(1)} / 10
                    </span>
                  </div>
                ))}
              </div>

              {movie.showtimes.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium">Available Showtimes:</h4>
                  <div className="space-y-1">
                    {movie.showtimes.map((showtime, idx) => (
                      <p key={idx} className="text-sm text-gray-600">
                        {new Date(showtime.start).toLocaleString()} at {showtime.cinema}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {recommendations.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No recommendations available
        </p>
      )}
    </div>
  );
}