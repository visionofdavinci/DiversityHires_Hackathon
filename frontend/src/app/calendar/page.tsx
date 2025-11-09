'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { NavLayout } from '@/components/nav-layout'

interface CalendarEvent {
  title: string
  start: string
  end: string
}

export default function CalendarPage() {
  const searchParams = useSearchParams()
  const [username, setUsername] = useState('')
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(false)

  // Load saved calendar state from localStorage on mount
  useEffect(() => {
    const savedCalendarUsername = localStorage.getItem('calendarUsername')
    const savedCalendarAuthenticated = localStorage.getItem('calendarAuthenticated')
    
    if (savedCalendarUsername && savedCalendarAuthenticated === 'true') {
      setUsername(savedCalendarUsername)
      checkAuthentication(savedCalendarUsername).then((isAuth) => {
        if (isAuth) {
          setAuthenticated(true)
          fetchEvents(savedCalendarUsername)
        }
      })
    }
  }, [])

  // Check if user just returned from OAuth
  useEffect(() => {
    const authSuccess = searchParams.get('authenticated')
    const urlUsername = searchParams.get('username')
    const error = searchParams.get('error')
    
    if (error) {
      alert(`Authentication error: ${error}`)
      // Clear URL params
      window.history.replaceState({}, '', '/calendar')
      return
    }
    
    if (authSuccess === 'true' && urlUsername) {
      console.log('OAuth success detected, setting username:', urlUsername)
      setUsername(urlUsername)
      setAuthenticated(true)
      // Save to localStorage
      localStorage.setItem('calendarUsername', urlUsername)
      localStorage.setItem('calendarAuthenticated', 'true')
      fetchEvents(urlUsername)
      
      // Clear URL params after processing
      window.history.replaceState({}, '', '/calendar')
    }
  }, [searchParams])

  const checkAuthentication = async (user: string) => {
    try {
      const response = await fetch(`http://localhost:5000/calendar/${encodeURIComponent(user)}/check-auth`)
      const data = await response.json()
      return data.authenticated === true
    } catch (error) {
      console.error('Error checking authentication:', error)
      return false
    }
  }

  const startOAuthFlow = async (user: string) => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/calendar/auth/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: user })
      })
      
      const data = await response.json()
      
      if (data.error) {
        alert(`Error: ${data.error}`)
        return
      }
      
      // Open OAuth URL in new window
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    } catch (error) {
      console.error('Error starting OAuth flow:', error)
      alert('Error connecting to server.')
    } finally {
      setLoading(false)
    }
  }

  const fetchEvents = async (user: string) => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:5000/calendar/${encodeURIComponent(user)}/events`)
      const data = await response.json()
      
      if (data.needs_auth) {
        setAuthenticated(false)
        alert('Please authenticate with Google Calendar first.')
      } else if (data.error) {
        console.error('Error fetching events:', data.error)
        alert(`Error: ${data.error}`)
      } else {
        setEvents(data.events || [])
        setAuthenticated(true)
      }
    } catch (error) {
      console.error('Error fetching calendar data:', error)
      alert('Error connecting to server.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCheckingAuth(true)
    
    // First check if user is already authenticated
    const isAuthenticated = await checkAuthentication(username)
    
    if (isAuthenticated) {
      setAuthenticated(true)
      // Save to localStorage
      localStorage.setItem('calendarUsername', username)
      localStorage.setItem('calendarAuthenticated', 'true')
      await fetchEvents(username)
    } else {
      // Start OAuth flow
      await startOAuthFlow(username)
    }
    
    setCheckingAuth(false)
  }

  if (!authenticated) {
    return (
      <NavLayout>
        <div className="flex items-center justify-center h-screen text-white">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
            <h1 className="text-2xl font-bold mb-6">Connect Google Calendar</h1>
            <p className="text-gray-400 mb-6">
              Enter your username and authenticate with Google to view your calendar events.
            </p>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="username" className="block text-sm font-medium mb-2">
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g., sanne, noor, ioana"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-2">
                  This will be used to save your calendar authentication.
                </p>
              </div>
              <button
                type="submit"
                disabled={loading || checkingAuth}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading || checkingAuth ? 'Checking...' : 'Connect Google Calendar'}
              </button>
            </form>
          </div>
        </div>
      </NavLayout>
    )
  }

  // Group events by date
  const groupedEvents = events.reduce((acc, event) => {
    const date = new Date(event.start).toLocaleDateString()
    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(event)
    return acc
  }, {} as Record<string, CalendarEvent[]>)

  return (
    <NavLayout>
      <div className="p-8 text-white overflow-auto h-screen">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Your Calendar - {username}</h1>
          <button
            onClick={() => {
              setAuthenticated(false)
              setEvents([])
              setUsername('')
              // Clear localStorage
              localStorage.removeItem('calendarUsername')
              localStorage.removeItem('calendarAuthenticated')
              // Clear URL params
              window.history.replaceState({}, '', '/calendar')
            }}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
          >
            Change Account
          </button>
        </div>
        {Object.entries(groupedEvents).length > 0 ? (
          Object.entries(groupedEvents).map(([date, events]) => (
            <div key={date} className="mb-8">
              <h2 className="text-xl font-semibold mb-4">{date}</h2>
              <div className="grid gap-4">
                {events.map((event, index) => (
                  <div
                    key={index}
                    className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold">{event.title}</h3>
                        <p className="text-gray-400">
                          {new Date(event.start).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                          {' - '}
                          {new Date(event.end).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-400">No upcoming events found.</p>
        )}
      </div>
    </NavLayout>
  )
}