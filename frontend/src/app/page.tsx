'use client'

import { Chat } from '@/components/chat'
import { ChatHistory } from '@/components/ChatHistory'
import { MovieCard } from '@/components/movie-card'
import { NavLayout } from '@/components/nav-layout'
import { useState, useEffect } from 'react'
import { Message } from '@/lib/types'

import CalendarView from '@/components/CalendarView'
import LetterboxdProfile from '@/components/LetterboxdProfile'
import CinevilleRecommendations from '@/components/CinevilleRecommendations'
import { CalendarSlot, MovieRecommendation } from '@/types'
import { ChevronRight, ChevronLeft, Plus, Clock } from 'lucide-react'

interface Movie {
  title: string
  year: number
  posterUrl?: string
  score: number
  showtimes?: Array<{ cinema: string; start: string }>
  userScores?: Record<string, number>
  tmdbData?: any
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [recommendations, setRecommendations] = useState<Movie[]>([])
  const [username, setUsername] = useState('')
  const [usernames, setUsernames] = useState<string[]>([])
  const [freeSlots, setFreeSlots] = useState<CalendarSlot[]>([])
  const [showCalendar, setShowCalendar] = useState(false)
  const [showRightPanel, setShowRightPanel] = useState(true)
  const [showChatHistory, setShowChatHistory] = useState(false)

  // Load state from localStorage on mount
  useEffect(() => {
    const savedUsernames = localStorage.getItem('movieMatcher_usernames')
    const savedMessages = localStorage.getItem('movieMatcher_messages')
    const savedShowCalendar = localStorage.getItem('movieMatcher_showCalendar')
    const savedRecommendations = localStorage.getItem('movieMatcher_recommendations')
    const savedRecommendationsKey = localStorage.getItem('movieMatcher_recommendationsKey')
    
    if (savedUsernames) {
      try {
        const parsedUsernames = JSON.parse(savedUsernames)
        setUsernames(parsedUsernames)
        
        // Load recommendations if they match the current usernames
        if (savedRecommendations && savedRecommendationsKey) {
          const currentKey = parsedUsernames.sort().join(',')
          if (currentKey === savedRecommendationsKey) {
            setRecommendations(JSON.parse(savedRecommendations))
            console.log('Loaded cached recommendations for:', currentKey)
          }
        }
      } catch (e) {
        console.error('Failed to parse saved usernames', e)
      }
    }
    
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages))
      } catch (e) {
        console.error('Failed to parse saved messages', e)
      }
    }
    
    if (savedShowCalendar) {
      setShowCalendar(savedShowCalendar === 'true')
    }
  }, [])

  // Save usernames to localStorage whenever they change
  useEffect(() => {
    if (usernames.length > 0) {
      localStorage.setItem('movieMatcher_usernames', JSON.stringify(usernames))
    } else {
      localStorage.removeItem('movieMatcher_usernames')
    }
  }, [usernames])

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('movieMatcher_messages', JSON.stringify(messages))
    }
  }, [messages])

  // Save recommendations to localStorage whenever they change
  useEffect(() => {
    if (recommendations.length > 0 && usernames.length > 0) {
      const usernamesKey = usernames.sort().join(',')
      localStorage.setItem('movieMatcher_recommendations', JSON.stringify(recommendations))
      localStorage.setItem('movieMatcher_recommendationsKey', usernamesKey)
      console.log('Saved recommendations for:', usernamesKey)
    }
  }, [recommendations, usernames])

  // Save calendar visibility
  useEffect(() => {
    localStorage.setItem('movieMatcher_showCalendar', showCalendar.toString())
  }, [showCalendar])

  const saveCurrentChatToHistory = () => {
    if (messages.length === 0) return

    const history = localStorage.getItem('movieMatcher_chatHistory')
    let sessions = history ? JSON.parse(history) : []

    // Get preview from first user message
    const firstUserMessage = messages.find(m => m.role === 'user')
    const preview = firstUserMessage?.content.slice(0, 60) || 'New conversation'

    const newSession = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      messages: messages,
      preview: preview + (firstUserMessage && firstUserMessage.content.length > 60 ? '...' : '')
    }

    sessions.unshift(newSession) // Add to beginning
    
    // Keep only last 20 sessions
    if (sessions.length > 20) {
      sessions = sessions.slice(0, 20)
    }

    localStorage.setItem('movieMatcher_chatHistory', JSON.stringify(sessions))
  }

  const handleNewChat = () => {
    if (messages.length > 0) {
      const confirmed = confirm('Start a new chat? Current conversation will be saved to history.')
      if (!confirmed) return
      
      saveCurrentChatToHistory()
    }
    
    setMessages([])
    localStorage.removeItem('movieMatcher_messages')
  }

  const handleLoadChatHistory = (loadedMessages: Message[]) => {
    // Save current chat before loading a new one
    if (messages.length > 0) {
      saveCurrentChatToHistory()
    }
    
    setMessages(loadedMessages)
    localStorage.setItem('movieMatcher_messages', JSON.stringify(loadedMessages))
  }

  // Extract Letterboxd usernames from text
  const extractUsernames = (text: string): string[] => {
    // Match both @mentions and plain usernames
    const mentionRegex = /@(\w+)/g;
    const letterboxdRegex = /letterboxd\.com\/([^\/\s]+)/g;
    const usernameRegex = /(?:user|profile|account):\s*(\w+)/gi;

    const usernames = new Set<string>();
    
    // Extract @mentions
    let match;
    while ((match = mentionRegex.exec(text)) !== null) {
      usernames.add(match[1].toLowerCase());
    }
    
    // Extract Letterboxd URLs
    while ((match = letterboxdRegex.exec(text)) !== null) {
      usernames.add(match[1].toLowerCase());
    }
    
    // Extract explicit username mentions
    while ((match = usernameRegex.exec(text)) !== null) {
      usernames.add(match[1].toLowerCase());
    }

    return Array.from(usernames);
  };

  const handleSendMessage = async (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user'
    }

    // Extract usernames from the message
    const detectedUsernames = extractUsernames(content);
    
    // Add any new usernames to the state
    if (detectedUsernames.length > 0) {
      const newUsernames = detectedUsernames.filter(
        name => !usernames.includes(name)
      );
      if (newUsernames.length > 0) {
        setUsernames(prev => [...prev, ...newUsernames]);
      }
    }

    setMessages(prev => [...prev, newMessage])
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, newMessage],
          usernames: usernames.concat(detectedUsernames)
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.content,
        role: 'assistant',
        actions: data.actions || [],  // Include agent actions
        intents: data.intents || []    // Include detected intents
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update recommendations if received
      if (data.recommendations?.length > 0) {
        setRecommendations(data.recommendations)
      }
      
      // Auto-open panel if agent suggests it
      if (data.actions?.some((a: any) => a.type === 'suggestion') && !showRightPanel) {
        setShowRightPanel(true)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (username && !usernames.includes(username)) {
      setUsernames([...usernames, username]);
      setUsername('');
    }
  };

  const handleRemoveUser = (userToRemove: string) => {
    setUsernames(usernames.filter(u => u !== userToRemove));
  };

  return (
    <NavLayout>
      <ChatHistory 
        isOpen={showChatHistory}
        onClose={() => setShowChatHistory(false)}
        onLoadSession={handleLoadChatHistory}
      />
      
      <div className="h-full flex flex-col">
        {/* User Management Bar */}
        <div className="bg-gray-800 p-4 border-b border-gray-700">
          <form onSubmit={handleAddUser} className="flex gap-4">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter Letterboxd username"
              className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add User
            </button>
            <button
              type="button"
              onClick={handleNewChat}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2"
              title="Start new chat"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </button>
            <button
              type="button"
              onClick={() => setShowChatHistory(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2"
              title="View chat history"
            >
              <Clock className="h-4 w-4" />
              History
            </button>
            <button
              type="button"
              onClick={() => setShowCalendar(!showCalendar)}
              className={`px-6 py-2 rounded-lg transition-colors ${
                showCalendar 
                  ? 'bg-purple-600 hover:bg-purple-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
              } text-white`}
            >
              {showCalendar ? 'Hide Calendar' : 'Show Calendar'}
            </button>
            <button
              type="button"
              onClick={() => setShowRightPanel(!showRightPanel)}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-2"
              title={showRightPanel ? "Hide panel" : "Show panel"}
            >
              {showRightPanel ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              {showRightPanel ? 'Hide' : 'Show'} Panel
            </button>
          </form>

          {/* User List */}
          <div className="flex flex-wrap gap-2 mt-2">
            {usernames.map(name => (
              <div
                key={name}
                className="inline-flex items-center gap-2 px-3 py-1 bg-gray-700 text-white rounded-full"
              >
                <span>{name}</span>
                <button
                  onClick={() => handleRemoveUser(name)}
                  className="text-gray-300 hover:text-red-500 text-lg leading-none"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden relative min-h-0">
          {/* Chat and Calendar Section */}
          <div className={`flex flex-col border-r border-gray-700 transition-all duration-300 h-full overflow-hidden ${
            showRightPanel ? 'flex-1' : 'w-full'
          }`}>
            {showCalendar && usernames.length > 0 && (
              <div className="flex-shrink-0 border-b border-gray-700 p-4 bg-gray-800 max-h-64 overflow-y-auto">
                <CalendarView
                  username={usernames[0]}
                  onSlotsUpdate={setFreeSlots}
                />
              </div>
            )}
            <div className="flex-1 min-h-0 overflow-hidden">
              <Chat
                messages={messages}
                isLoading={isLoading}
                onSubmit={handleSendMessage}
                onPanelToggle={() => setShowRightPanel(!showRightPanel)}
                className="h-full"
              />
            </div>
          </div>

          {/* Recommendations and Profiles Section - Retractable */}
          <div className={`flex flex-col h-full bg-gray-800 transition-all duration-300 overflow-hidden ${
            showRightPanel ? 'w-96' : 'w-0'
          }`}>
            <div className="flex-1 overflow-y-auto">
              {/* Movie Recommendations */}
              {usernames.length > 0 && (
                <div className="p-4">
                  <h3 className="text-white text-lg font-semibold mb-4">Movie Recommendations</h3>
                  <CinevilleRecommendations
                    usernames={usernames}
                    options={{
                      useCalendar: true,
                      limitAmsterdam: true,
                      daysAhead: 7,
                      maxResults: 10
                    }}
                  />
                </div>
              )}

              {/* Letterboxd Profiles */}
              {usernames.map(name => (
                <div key={name} className="p-4 border-t border-gray-700">
                  <LetterboxdProfile username={name} />
                </div>
              ))}

              {usernames.length === 0 && (
                <div className="p-4 text-center text-gray-400">
                  <p className="text-sm">Add users to see recommendations and profiles</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </NavLayout>
  );
}