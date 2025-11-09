'use client'

import { useState, useEffect } from 'react'

interface MovieEntry {
  title: string
  rating: number
  watchedDate: string
  review?: string
}

export default function LetterboxdPage() {
  const [movies, setMovies] = useState<MovieEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Replace with actual API call to your backend
    const fetchLetterboxdData = async () => {
      try {
        const response = await fetch('/api/letterboxd')
        const data = await response.json()
        setMovies(data)
      } catch (error) {
        console.error('Error fetching Letterboxd data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchLetterboxdData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
      </div>
    )
  }

  return (
    <div className="p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Your Letterboxd History</h1>
      <div className="grid gap-4">
        {movies.length > 0 ? (
          movies.map((movie, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">{movie.title}</h3>
                  <p className="text-gray-400">
                    Watched on {new Date(movie.watchedDate).toLocaleDateString()}
                  </p>
                </div>
                <div className="bg-gray-700 px-2 py-1 rounded">
                  {movie.rating}/5
                </div>
              </div>
              {movie.review && (
                <p className="mt-2 text-gray-300">{movie.review}</p>
              )}
            </div>
          ))
        ) : (
          <p className="text-gray-400">No Letterboxd history found.</p>
        )}
      </div>
    </div>
  )
}