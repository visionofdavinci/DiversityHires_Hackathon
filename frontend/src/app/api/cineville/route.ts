import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Make a request to your Python backend
    const response = await fetch('http://localhost:5000/api/cineville', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch Cineville data')
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Cineville API error:', error)
    
    // For development, return mock data
    const mockData = [
      {
        title: 'Poor Things',
        location: 'Amsterdam',
        theater: 'Eye Filmmuseum',
        showtime: '2025-11-10T20:30:00Z'
      },
      {
        title: 'The Zone of Interest',
        location: 'Amsterdam',
        theater: 'Kriterion',
        showtime: '2025-11-10T21:00:00Z'
      },
      {
        title: 'Perfect Days',
        location: 'Amsterdam',
        theater: 'Rialto VU',
        showtime: '2025-11-11T19:15:00Z'
      },
      {
        title: 'The Boy and the Heron',
        location: 'Amsterdam',
        theater: 'The Movies',
        showtime: '2025-11-11T20:45:00Z'
      }
    ]

    return NextResponse.json(mockData)
  }
}