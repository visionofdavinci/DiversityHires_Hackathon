import { NextResponse } from 'next/server'
import { api } from '@/services/api'
import { Message } from '@/lib/types'

// Hugging Face Inference API - Free and open source!
const HF_API_KEY = process.env.HUGGINGFACE_API_KEY || 'hf_demo_key'
const HF_MODEL = 'mistralai/Mistral-7B-Instruct-v0.2' // Free model

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

// Alternative free models you can use:
// - 'meta-llama/Llama-2-7b-chat-hf'
// - 'HuggingFaceH4/zephyr-7b-beta'
// - 'microsoft/DialoGPT-large'

async function queryHuggingFace(messages: any[]) {
  // Get only the last few messages to stay within token limits
  const recentMessages = messages.slice(-5)
  
  // Format messages for the model - create a conversational prompt
  const prompt = recentMessages.map(msg => {
    if (msg.role === 'system') return msg.content
    if (msg.role === 'user') return `User: ${msg.content}`
    return `Assistant: ${msg.content}`
  }).join('\n\n') + '\n\nAssistant:'

  const response = await fetch(
    `https://router.huggingface.co/hf-inference/models/${HF_MODEL}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${HF_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: 300,
          temperature: 0.8,
          top_p: 0.95,
          repetition_penalty: 1.2,
          return_full_text: false,
          do_sample: true
        }
      })
    }
  )

  if (!response.ok) {
    // Fallback to a simpler response if API fails
    console.error('HuggingFace API error:', await response.text())
    throw new Error('Failed to get response from AI model')
  }

  const data = await response.json()
  
  // Handle different response formats
  let generatedText = ''
  if (Array.isArray(data) && data[0]?.generated_text) {
    generatedText = data[0].generated_text
  } else if (data.generated_text) {
    generatedText = data.generated_text
  } else if (data.error) {
    throw new Error(data.error)
  }
  
  // Clean up the response (remove any repeated text or artifacts)
  generatedText = generatedText.trim()
    .replace(/^(User:|Assistant:)/gm, '')
    .trim()
  
  return generatedText || "I'm here to help! Try asking me about movies or adding some Letterboxd usernames."
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
    
    // Detect what the user wants to do
    const intents = detectIntent(lastMessage.content)
    const actions: AgentAction[] = []
    
    let movieData = '';
    let calendarData = '';
    
    // PROACTIVE ACTION: Auto-fetch relevant data based on intent
    if (usernames.length > 0) {
      try {
        // Always fetch recommendations if we have usernames
        const recommendations = await api.getMovieRecommendations(usernames, {
          useCalendar: true,
          limitAmsterdam: true,
          daysAhead: intents.includes('urgent_timeframe') ? 2 : 7,
        });
        movieData = formatMovieData(recommendations);
        
        // ACTION: Proactively suggest viewing recommendations
        if (recommendations.length > 0 && intents.includes('find_movies')) {
          actions.push({
            type: 'suggestion',
            description: `I found ${recommendations.length} movies matching your group's preferences! Check the panel on the right →`,
            data: { recommendationCount: recommendations.length }
          })
        }
        
        // ACTION: Fetch calendar if user asks about availability
        if (intents.includes('check_calendar') && usernames[0]) {
          try {
            const slots = await api.getCalendarFreeSlots(usernames[0]);
            calendarData = slots.length > 0 
              ? `Available times:\n${slots.slice(0, 3).map(slot => 
                  `${new Date(slot.start).toLocaleString()} - ${new Date(slot.end).toLocaleString()}`
                ).join('\n')}`
              : 'No free time slots found.';
            
            actions.push({
              type: 'navigation',
              description: 'Navigate to Calendar page to see full availability',
              data: { page: '/calendar' }
            })
          } catch (e) {
            console.log('Calendar not available')
          }
        }
        
        // ACTION: Suggest genre filter if user mentions genre
        if (intents.includes('genre_preference')) {
          const genres = ['comedy', 'drama', 'action', 'horror', 'thriller', 'romance']
          const mentionedGenre = genres.find(g => lastMessage.content.toLowerCase().includes(g))
          if (mentionedGenre) {
            actions.push({
              type: 'filter',
              description: `Filtering for ${mentionedGenre} movies`,
              data: { mood: mentionedGenre }
            })
          }
        }
        
      } catch (error) {
        console.error('API error:', error);
      }
    } else {
      // ACTION: Prompt user to add usernames if they haven't
      if (intents.includes('find_movies')) {
        actions.push({
          type: 'suggestion',
          description: 'Add Letterboxd usernames first using the "Add User" button above to get personalized recommendations!',
          data: null
        })
      }
    }

    // Enhance the user's message with context
    const systemPrompt = movieData || calendarData
      ? `You are a friendly movie recommendation assistant helping friends find movies to watch together.

Current movie recommendations available:
${movieData || 'None yet - ask users to add their Letterboxd usernames'}

Calendar availability:
${calendarData || 'No calendar data loaded yet'}

Be helpful, concise, and enthusiastic! Suggest movies from the recommendations when relevant. If asked about capabilities, mention that you can help with Letterboxd preferences, calendar availability, and Cineville showtimes in Amsterdam.`
      : `You are a friendly movie recommendation assistant. You can help users find movies to watch together!

Your capabilities:
- Check Letterboxd movie preferences (users should add their usernames with "Add user" button)
- View calendar availability  
- Find Cineville showtimes in Amsterdam
- Recommend movies based on group preferences

Be friendly and guide users on how to use the app. Keep responses brief and helpful.`

    const enhancedMessages = [
      {
        role: 'system',
        content: systemPrompt
      },
      ...messages.slice(-5) // Only send last 5 messages for context
    ];

    // Get AI response from Hugging Face
    let aiResponse;
    try {
      aiResponse = await queryHuggingFace(enhancedMessages);
    } catch (error) {
      // Fallback response if AI fails
      console.error('AI error:', error);
      
      // Create contextual fallback based on user message
      const userMessage = messages[messages.length - 1].content.toLowerCase()
      
      if (userMessage.includes('hello') || userMessage.includes('hi')) {
        aiResponse = "Hi! 👋 I can help you find movies to watch with friends. Add some Letterboxd usernames using the button above to get started!"
      } else if (userMessage.includes('help') || userMessage.includes('what can you do')) {
        aiResponse = "I can help you find movies based on:\n• Letterboxd preferences\n• Calendar availability\n• Cineville showtimes in Amsterdam\n\nTry adding some usernames with the 'Add User' button!"
      } else if (usernames.length > 0 && movieData) {
        aiResponse = `Based on your group's preferences, here are some recommendations:\n\n${movieData}`
      } else {
        aiResponse = "I'm here to help you find movies! Add some Letterboxd usernames to get personalized recommendations for your group."
      }
    }

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
      content: aiResponse,
      recommendations: movieRecommendations,
      actions: actions, // Return proactive actions the agent wants to take
      intents: intents   // Return detected intents for debugging/UI
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { 
        content: "I'm having trouble processing your request right now. Please try again!",
        error: 'There was an error processing your request' 
      },
      { status: 500 }
    );
  }
}