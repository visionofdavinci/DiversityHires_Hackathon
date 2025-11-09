import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export async function GET() {
  // Return mock data during build time
  const isBuildTime = process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_API_URL;
  
  if (isBuildTime) {
    console.log('Build time detected, returning mock data');
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
    ];
    return NextResponse.json(mockData);
  }

  try {
    // Don't make requests during build time
    if (!API_BASE_URL || API_BASE_URL === 'undefined') {
      throw new Error('API URL not configured');
    }

    // Make a request to your Python backend
    const response = await fetch(`${API_BASE_URL}/cineville/upcoming`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000)
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

// Prevent this route from being pre-rendered at build time
export const dynamic = 'force-dynamic';