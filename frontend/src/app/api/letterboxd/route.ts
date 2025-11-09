import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Make a request to your Python backend
    const response = await fetch('http://localhost:5000/api/letterboxd', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch Letterboxd data')
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Letterboxd API error:', error)
    
    // For development, return mock data
    const mockData = [
      {
        title: 'Oppenheimer',
        rating: 4.5,
        watchedDate: '2023-07-21',
        review: 'A masterpiece of biographical filmmaking.'
      },
      {
        title: 'Barbie',
        rating: 4.0,
        watchedDate: '2023-07-22',
        review: 'Surprisingly deep and entertaining.'
      },
      {
        title: 'Poor Things',
        rating: 4.8,
        watchedDate: '2023-12-25',
        review: 'Yorgos Lanthimos at his best.'
      }
    ]

    return NextResponse.json(mockData)
  }
}