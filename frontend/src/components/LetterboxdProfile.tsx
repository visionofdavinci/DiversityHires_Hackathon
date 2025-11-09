import { useState, useEffect } from 'react';
import { UserProfile } from '@/types';
import { api } from '@/services/api';

interface LetterboxdProfileProps {
  username: string;
}

export default function LetterboxdProfile({ username }: LetterboxdProfileProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await api.getUserProfile(username);
        setProfile(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [username]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900 text-red-200 rounded-lg text-sm">
        <p>{error}</p>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-white">{profile.username}'s Profile</h2>
          <p className="text-gray-400 text-sm">Letterboxd Ratings</p>
        </div>
      </div>

      <div className="grid gap-3">
        {profile.ratings.map((rating, index) => (
          <div
            key={index}
            className="p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-medium text-white text-sm">
                  {rating.movieTitle}
                  {rating.year && <span className="text-gray-400"> ({rating.year})</span>}
                </h3>
              </div>
              <div className="flex items-center space-x-1">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-4 h-4 ${
                      i < rating.rating
                        ? 'text-yellow-400'
                        : 'text-gray-500'
                    }`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {profile.ratings.length === 0 && (
        <p className="text-gray-400 text-center py-6 text-sm">
          No ratings available
        </p>
      )}
    </div>
  );
}