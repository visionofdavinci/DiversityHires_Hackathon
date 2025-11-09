'use client'

import { useState, useEffect } from 'react'

interface CinevilleMovie {
  title: string
  location: string
  showtime: string
  theater: string
}

export default function CinevillePage() {
  const [movies, setMovies] = useState<CinevilleMovie[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Replace with actual API call to your backend
    const fetchCinevilleData = async () => {
      try {
        const response = await fetch('/api/cineville')
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
      <div className="flex items-center justify-center h-screen text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
      </div>
    )
  }

  // Group movies by date
  const groupedMovies = movies.reduce((acc, movie) => {
    const date = new Date(movie.showtime).toLocaleDateString()
    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(movie)
    return acc
  }, {} as Record<string, CinevilleMovie[]>)

  return (
    <div className="p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Cineville Showtimes</h1>
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
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold">{movie.title}</h3>
                      <p className="text-gray-400">{movie.theater}</p>
                      <p className="text-gray-400">{movie.location}</p>
                    </div>
                    <div className="bg-gray-700 px-2 py-1 rounded">
                      {new Date(movie.showtime).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      ) : (
        <p className="text-gray-400">No upcoming showings found.</p>
      )}
    </div>
  )
}