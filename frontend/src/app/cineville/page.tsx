'use client'

import { useState, useEffect } from 'react'
import { NavLayout } from '@/components/nav-layout'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface CinevilleMovie {
  title: string
  location: string
  showtime: string
  theater: string
  year?: number
  genres?: string[]
  overview?: string
}

export default function CinevillePage() {
  const [movies, setMovies] = useState<CinevilleMovie[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCinevilleData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/cineville/upcoming`)
        const data = await response.json()
        setMovies(data)
      } catch (error) {
        console.error('Error fetching Cineville data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCinevilleData()
  }, [])

  if (loading) {
    return (
      <NavLayout>
        <div className="flex items-center justify-center h-screen text-white">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
        </div>
      </NavLayout>
    )
  }

  // Group movies by date
  const groupedMovies = movies.reduce((acc, movie) => {
    const dateObj = new Date(movie.showtime);
    // Check if date is valid
    if (isNaN(dateObj.getTime())) {
      console.warn('Invalid showtime:', movie.showtime);
      return acc;
    }
    
    const date = dateObj.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(movie)
    return acc
  }, {} as Record<string, CinevilleMovie[]>)

  return (
    <NavLayout>
      <div className="p-8 text-white overflow-auto h-screen">
        <h1 className="text-2xl font-bold mb-6">Cineville Showtimes - Next 7 Days</h1>
        {Object.entries(groupedMovies).length > 0 ? (
          Object.entries(groupedMovies).map(([date, movies]) => (
            <div key={date} className="mb-8">
              <h2 className="text-xl font-semibold mb-4">{date}</h2>
              <div className="grid gap-4">
                {movies.map((movie, index) => (
                  <div
                    key={index}
                    className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold">
                          {movie.title}
                          {movie.year && <span className="text-gray-400 ml-2">({movie.year})</span>}
                        </h3>
                        <p className="text-gray-400">
                          📍 {movie.theater}, Amsterdam
                        </p>
                      </div>
                      <div className="bg-gray-700 px-3 py-1 rounded text-sm">
                        {new Date(movie.showtime).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    </div>
                    
                    {/* Genres */}
                    {movie.genres && movie.genres.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {movie.genres.map((genre, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-blue-600/30 text-blue-300 rounded text-xs"
                          >
                            {genre}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {/* Overview */}
                    {movie.overview && (
                      <p className="text-gray-400 text-sm line-clamp-2">
                        {movie.overview}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-400">No upcoming showings found.</p>
        )}
      </div>
    </NavLayout>
  )
}