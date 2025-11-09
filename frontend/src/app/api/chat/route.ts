import { NextResponse } from 'next/server'
import { api } from '@/services/api'
import { Message } from '@/lib/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Agent action types
type AgentAction = {
  type: 'suggestion' | 'data_fetch' | 'navigation' | 'filter'
  description: string
  data?: any
}

// Detect user intent from message
function detectIntent(message: string): string[] {
  const msg = message.toLowerCase()
  const intents: string[] = []
  
  if (msg.includes('calendar') || msg.includes('when') || msg.includes('free time') || msg.includes('available')) {
    intents.push('check_calendar')
  }
  if (msg.includes('movie') || msg.includes('film') || msg.includes('watch')) {
    intents.push('find_movies')
  }
  if (msg.includes('tonight') || msg.includes('today') || msg.includes('tomorrow')) {
    intents.push('urgent_timeframe')
  }
  if (msg.includes('comedy') || msg.includes('drama') || msg.includes('action') || msg.includes('horror')) {
    intents.push('genre_preference')
  }
  if (msg.includes('best') || msg.includes('top') || msg.includes('highest rated')) {
    intents.push('quality_filter')
  }
  
  return intents
}

// Helper function to extract usernames from messages
function extractUsernames(messages: Message[]): string[] {
  const usernames = new Set<string>();
  const usernameRegex = /@(\w+)/g;
  
  messages.forEach(message => {
    const matches = message.content.matchAll(usernameRegex);
    for (const match of matches) {
      usernames.add(match[1]);
    }
  });
  
  return Array.from(usernames);
}

// Call your Flask backend's Gemini-powered /chat endpoint
async function queryGeminiBackend(userMessage: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: userMessage
    }),
    // Add timeout
    signal: AbortSignal.timeout(30000)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Backend chat request failed');
  }

  return await response.json();
}

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const lastMessage = messages[messages.length - 1];
    const usernames = extractUsernames(messages);
    
    // Detect what the user wants to do
    const intents = detectIntent(lastMessage.content)
    const actions: AgentAction[] = []
    
    let aiResponse: string;
    let movieRecommendations: any[] = [];

    try {
      // Call your Flask backend's Gemini-powered chat endpoint
      const backendResponse = await queryGeminiBackend(lastMessage.content);
      
      // Extract the Gemini-generated message
      aiResponse = backendResponse.message;
      
      // Extract recommendations from backend response
      const recs = backendResponse.recommendations || [];
      
      movieRecommendations = recs.map((movie: any) => ({
        title: movie.title,
        year: movie.year || new Date().getFullYear(),
        score: movie.group_score * 5, // Convert to 0-10 scale
        posterUrl: movie.tmdb?.poster_path 
          ? `https://image.tmdb.org/t/p/w500${movie.tmdb.poster_path}`
          : undefined,
        showtimes: movie.showtimes,
        userScores: movie.per_user_scores,
        tmdbData: movie.tmdb
      }));

      // Add action if recommendations found
      if (movieRecommendations.length > 0) {
        actions.push({
          type: 'suggestion',
          description: `Found ${movieRecommendations.length} movies! Check them out on the right →`,
          data: { recommendationCount: movieRecommendations.length }
        })
      }

    } catch (error) {
      console.error('Backend chat error:', error);
      
      // Fallback response if backend fails
      const userMessage = lastMessage.content.toLowerCase()
      
      if (userMessage.includes('hello') || userMessage.includes('hi')) {
        aiResponse = "Hi! 👋 I can help you find movies to watch with friends. Try asking something like 'Find a movie for sanne and ioana this Friday. Mood: comedy.'"
      } else if (userMessage.includes('help') || userMessage.includes('what can you do')) {
        aiResponse = "I can help you find movies! Just tell me:\n• Who's watching (names like sanne, noor, ioana)\n• When (Friday, tomorrow, this weekend)\n• What mood (comedy, action, drama, etc.)\n\nExample: 'Movie Friday with sanne and noor, comedy mood'"
      } else {
        aiResponse = "I'm here to help you find movies! Try saying something like: 'Find a movie for sanne and ioana this Friday. Mood: comedy.'"
      }

      // Try to fetch recommendations separately if backend chat failed
      if (usernames.length > 0) {
        try {
          const recs = await api.getMovieRecommendations(usernames, {
            useCalendar: true,
            limitAmsterdam: true,
            daysAhead: 7,
          });
          
          movieRecommendations = recs.map((movie: any) => ({
            title: movie.title,
            year: movie.year || new Date().getFullYear(),
            score: movie.group_score * 5,
            posterUrl: movie.tmdb?.poster_path 
              ? `https://image.tmdb.org/t/p/w500${movie.tmdb.poster_path}`
              : undefined,
            showtimes: movie.showtimes,
            userScores: movie.per_user_scores,
            tmdbData: movie.tmdb
          }));
        } catch (recError) {
          console.error('Error fetching recommendations:', recError);
        }
      }
    }

    return NextResponse.json({
      content: aiResponse,
      recommendations: movieRecommendations,
      actions: actions,
      intents: intents
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { 
        content: "I'm having trouble right now. Try asking like: 'Movie Friday with sanne and ioana, comedy mood'",
        error: 'There was an error processing your request' 
      },
      { status: 500 }
    );
  }
}

// Prevent this route from being pre-rendered at build time
export const dynamic = 'force-dynamic';