'use client'

import { useState, useEffect } from 'react'

interface CalendarEvent {
  id: string
  title: string
  start: string
  end: string
  description?: string
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Replace with actual API call to your backend
    const fetchCalendarData = async () => {
      try {
        const response = await fetch('/api/calendar')
        const data = await response.json()
        setEvents(data)
      } catch (error) {
        console.error('Error fetching calendar data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCalendarData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
      </div>
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
    <div className="p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Your Calendar</h1>
      {Object.entries(groupedEvents).length > 0 ? (
        Object.entries(groupedEvents).map(([date, events]) => (
          <div key={date} className="mb-8">
            <h2 className="text-xl font-semibold mb-4">{date}</h2>
            <div className="grid gap-4">
              {events.map((event) => (
                <div
                  key={event.id}
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
                  {event.description && (
                    <p className="mt-2 text-gray-300">{event.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))
      ) : (
        <p className="text-gray-400">No upcoming events found.</p>
      )}
    </div>
  )
}