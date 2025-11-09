import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Make a request to your Python backend
    const response = await fetch('http://localhost:5000/api/calendar', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch calendar data')
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Calendar API error:', error)
    
    // For development, return mock data
    const mockData = [
      {
        id: '1',
        title: 'Movie Night: Perfect Days',
        start: '2025-11-11T19:15:00Z',
        end: '2025-11-11T21:30:00Z',
        description: 'At Rialto VU with friends'
      },
      {
        id: '2',
        title: 'Dinner before movie',
        start: '2025-11-11T17:30:00Z',
        end: '2025-11-11T19:00:00Z',
        description: 'Restaurant near Rialto VU'
      },
      {
        id: '3',
        title: 'The Boy and the Heron screening',
        start: '2025-11-12T20:45:00Z',
        end: '2025-11-12T23:00:00Z',
        description: 'At The Movies Amsterdam'
      }
    ]

    return NextResponse.json(mockData)
  }
}