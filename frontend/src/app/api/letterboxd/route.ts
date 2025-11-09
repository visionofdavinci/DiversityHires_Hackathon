import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export async function GET() {
  try {
    // Don't make requests during build time
    if (!API_BASE_URL || API_BASE_URL === 'undefined') {
      throw new Error('API URL not configured');
    }

    // Make a request to your Python backend
    const response = await fetch(`${API_BASE_URL}/api/letterboxd`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000)
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

// Prevent this route from being pre-rendered at build time
export const dynamic = 'force-dynamic';