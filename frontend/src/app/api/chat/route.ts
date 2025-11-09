import OpenAI from 'openai'
import { NextResponse } from 'next/server'
import { api } from '@/services/api'
import { Message } from '@/lib/types'

// Create an OpenAI API client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

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

// Helper function to format movie data for the AI
function formatMovieData(recommendations: any[]): string {
  if (!recommendations.length) return 'No movies found matching the criteria.';
  
  return recommendations.slice(0, 3).map((movie: any) => {
    return `
      Title: ${movie.title} (${movie.year})
      Group Score: ${(movie.group_score * 5).toFixed(1)}/10
      Showtimes: ${movie.showtimes.map((st: any) => 
        `${new Date(st.start).toLocaleString()} at ${st.cinema}`
      ).join(', ')}
    `.trim();
  }).join('\n\n');
}

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const lastMessage = messages[messages.length - 1];
    const usernames = extractUsernames(messages);
    
    let movieData = '';
    let calendarData = '';
    
    // If usernames are mentioned, try to fetch relevant data
    if (usernames.length > 0) {
      try {
        const recommendations = await api.getMovieRecommendations(usernames, {
          useCalendar: true,
          limitAmsterdam: true,
          daysAhead: 7,
        });
        movieData = formatMovieData(recommendations);
        
        if (usernames[0]) {
          const slots = await api.getCalendarFreeSlots(usernames[0]);
          calendarData = slots.length > 0 
            ? `Available times:\n${slots.slice(0, 3).map(slot => 
                `${new Date(slot.start).toLocaleString()} - ${new Date(slot.end).toLocaleString()}`
              ).join('\n')}`
            : 'No free time slots found.';
        }
      } catch (error) {
        console.error('API error:', error);
      }
    }

    // Enhance the user's message with context
    const enhancedMessages = [
      {
        role: 'system',
        content: `You are a movie recommendation assistant. You can see movie recommendations and calendar availability for mentioned users.
                 When users mention someone with @username, you can see their data.
                 Current movie data: ${movieData || 'No movie data available'}
                 Current calendar data: ${calendarData || 'No calendar data available'}`
      },
      ...messages
    ];

    // Get AI response
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: enhancedMessages.map((message: any) => ({
        content: message.content,
        role: message.role,
      })),
    });

    // Convert Cineville recommendations to MovieCard format
    interface MovieRecommendation {
      title: string;
      year: number;
      score: number;
      posterUrl?: string;
      showtimes?: Array<{ cinema: string; start: string }>;
      userScores?: Record<string, number>;
      tmdbData?: any;
    }

    let movieRecommendations: MovieRecommendation[] = [];
    if (usernames.length > 0) {
      try {
        const recs = await api.getMovieRecommendations(usernames, {
          useCalendar: true,
          limitAmsterdam: true,
          daysAhead: 7,
        });
        
        movieRecommendations = recs.map(movie => ({
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
      } catch (error) {
        console.error('Error fetching recommendations:', error);
      }
    }

    return NextResponse.json({
      content: response.choices[0].message.content,
      recommendations: movieRecommendations
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'There was an error processing your request' },
      { status: 500 }
    );
  }
}