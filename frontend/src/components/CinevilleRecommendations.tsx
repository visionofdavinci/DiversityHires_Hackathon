import { useState, useEffect, useMemo, useRef } from 'react';
import { MovieRecommendation } from '@/types';
import { api } from '@/services/api';
import { RefreshCw } from 'lucide-react';

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
  
  // Track which username sets we've already fetched
  const fetchedUsernamesRef = useRef<Set<string>>(new Set());
  const usernamesKey = useMemo(() => usernames.sort().join(','), [usernames]);

  const fetchRecommendations = async (force = false) => {
    if (usernames.length === 0) {
      setRecommendations([]);
      return;
    }

    // Skip if we've already fetched and not forcing refresh
    if (!force && fetchedUsernamesRef.current.has(usernamesKey)) {
      console.log('Using cached recommendations for:', usernamesKey);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      console.log(force ? 'Force refreshing recommendations for:' : 'Fetching new recommendations for:', usernamesKey);
      const data = await api.getMovieRecommendations(usernames, options);
      setRecommendations(data);
      fetchedUsernamesRef.current.add(usernamesKey);
      
      // Save to localStorage
      localStorage.setItem('movieMatcher_cineville_recommendations', JSON.stringify(data))
      localStorage.setItem('movieMatcher_cineville_key', usernamesKey)
      console.log('Saved Cineville recommendations to localStorage')
    } catch (err) {
      console.error('Error loading recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setIsLoading(false);
    }
  }

  const handleRefresh = () => {
    // Clear cache and force refresh
    fetchedUsernamesRef.current.delete(usernamesKey)
    fetchRecommendations(true)
  }

  // Load cached recommendations from localStorage on mount
  useEffect(() => {
    const savedRecommendations = localStorage.getItem('movieMatcher_cineville_recommendations')
    const savedKey = localStorage.getItem('movieMatcher_cineville_key')
    
    if (savedRecommendations && savedKey === usernamesKey) {
      try {
        const parsed = JSON.parse(savedRecommendations)
        setRecommendations(parsed)
        fetchedUsernamesRef.current.add(usernamesKey)
        console.log('Loaded cached Cineville recommendations from localStorage for:', usernamesKey)
      } catch (e) {
        console.error('Failed to parse cached recommendations', e)
      }
    }
  }, [usernamesKey])

  useEffect(() => {
    fetchRecommendations(false)
  }, [usernamesKey]) // Only re-fetch when the username set changes

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/50 text-red-200 rounded-lg border border-red-700">
        <p className="font-semibold text-sm mb-1">⚠️ Could not load recommendations</p>
        <p className="text-xs">{error}</p>
        <p className="text-xs mt-2 text-red-300">
          • Make sure Flask backend is running on port 5000<br/>
          • Check that Letterboxd username '{usernames[0]}' exists<br/>
          • View browser console for details
        </p>
        <button
          onClick={handleRefresh}
          className="mt-3 px-3 py-1 bg-red-800 hover:bg-red-700 rounded text-xs flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Refresh Button */}
      <div className="flex justify-end">
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="px-3 py-1 bg-gray-600 hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded text-xs flex items-center gap-1 transition-colors"
          title="Refresh recommendations"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
      
      {recommendations.length === 0 ? (
        <p className="text-gray-400 text-center py-8 text-sm">
          Loading recommendations...
        </p>
      ) : (
        <div className="space-y-3">
          {recommendations.map((movie, index) => (
            <div
              key={index}
              className="bg-gray-700 rounded-lg p-3 hover:bg-gray-600 transition-colors"
            >
              <div>
                <h3 className="text-white font-semibold text-sm">
                  {movie.title}
                  {movie.year && <span className="text-gray-400"> ({movie.year})</span>}
                </h3>
                <p className="text-gray-300 text-xs mt-1">
                  Group Score: {(movie.group_score * 5).toFixed(1)} / 10
                </p>
              </div>

              {movie.showtimes && movie.showtimes.length > 0 && (
                <div className="mt-2 space-y-1">
                  {movie.showtimes.slice(0, 2).map((showtime, idx) => (
                    <p key={idx} className="text-xs text-gray-400">
                      {new Date(showtime.start).toLocaleDateString()} at {showtime.cinema}
                    </p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}