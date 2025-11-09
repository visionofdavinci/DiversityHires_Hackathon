'use client'

import { useState, useEffect } from 'react'
import { NavLayout } from '@/components/nav-layout'

interface MovieEntry {
  title: string
  rating: number
  year?: number
  liked?: boolean
  rewatch?: boolean
  source?: string
  watchedDate?: string
  genres?: string[]
  overview?: string
}

export default function LetterboxdPage() {
  const [username, setUsername] = useState('')
  const [movies, setMovies] = useState<MovieEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Load username from localStorage on mount
  useEffect(() => {
    const savedUsernames = localStorage.getItem('usernames')
    if (savedUsernames) {
      const parsed = JSON.parse(savedUsernames)
      if (parsed.length > 0) {
        setUsername(parsed[0])
        // Auto-load profile if username exists
        loadProfile(parsed[0])
      }
    }
  }, [])

  const loadProfile = async (user: string) => {
    if (!user) return
    
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/letterboxd/${encodeURIComponent(user)}`)
      const data = await response.json()
      
      if (data.error) {
        console.error('Error fetching Letterboxd data:', data.error)
        alert('Error fetching data. Please check the username and try again.')
      } else {
        setMovies(data.recent_movies || [])
        setSubmitted(true)
      }
    } catch (error) {
      console.error('Error fetching Letterboxd data:', error)
      alert('Error connecting to server.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Save username to localStorage (sync with home page)
    const existingUsernames = JSON.parse(localStorage.getItem('usernames') || '[]')
    if (!existingUsernames.includes(username)) {
      existingUsernames.push(username)
      localStorage.setItem('usernames', JSON.stringify(existingUsernames))
    }
    
    await loadProfile(username)
  }

  if (!submitted) {
    return (
      <NavLayout>
        <div className="flex items-center justify-center h-screen text-white">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
            <h1 className="text-2xl font-bold mb-6">Letterboxd Profile</h1>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="username" className="block text-sm font-medium mb-2">
                  Letterboxd Username
                </label>
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Load Profile'}
              </button>
            </form>
          </div>
        </div>
      </NavLayout>
    )
  }

  return (
    <NavLayout>
      <div className="p-8 text-white overflow-auto h-screen">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Letterboxd History - {username}</h1>
          <button
            onClick={() => {
              setSubmitted(false)
              setMovies([])
              setUsername('')
            }}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
          >
            Change User
          </button>
        </div>
        <div className="grid gap-4">
          {movies.length > 0 ? (
            movies.map((movie, index) => (
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
                    {movie.watchedDate && (
                      <p className="text-gray-400 text-sm">
                        Watched on {new Date(movie.watchedDate).toLocaleDateString()}
                      </p>
                    )}
                    {movie.source && (
                      <p className="text-gray-500 text-sm">Source: {movie.source}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {movie.rating !== undefined && movie.rating > 0 && (
                      <div className="bg-gray-700 px-2 py-1 rounded">
                        {'★'.repeat(movie.rating)}{'☆'.repeat(5 - movie.rating)}
                      </div>
                    )}
                    <div className="flex gap-2">
                      {movie.liked && (
                        <span className="text-red-500" title="Liked">❤️</span>
                      )}
                      {movie.rewatch && (
                        <span className="text-blue-500" title="Rewatch">🔄</span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Genres */}
                {movie.genres && movie.genres.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {movie.genres.map((genre, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-purple-600/30 text-purple-300 rounded text-xs"
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
            ))
          ) : (
            <p className="text-gray-400">No Letterboxd history found.</p>
          )}
        </div>
      </div>
    </NavLayout>
  )
}