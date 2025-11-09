'use client'

import { Chat } from '@/components/chat'
import { MovieCard } from '@/components/movie-card'
import { NavLayout } from '@/components/nav-layout'
import { useState } from 'react'
import { Message } from '@/lib/types'

import CalendarView from '@/components/CalendarView'
import LetterboxdProfile from '@/components/LetterboxdProfile'
import CinevilleRecommendations from '@/components/CinevilleRecommendations'
import { CalendarSlot, MovieRecommendation } from '@/types'

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
        role: 'assistant'
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update recommendations if received
      if (data.recommendations?.length > 0) {
        setRecommendations(data.recommendations)
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
      <div className="h-full flex flex-col">
        {/* User Management Bar */}
        <div className="bg-gray-800 p-4 border-b border-gray-700">
          <form onSubmit={handleAddUser} className="flex gap-4">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter Letterboxd username"
              className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add User
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
                  className="text-gray-300 hover:text-red-500"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 grid grid-cols-12 overflow-hidden">
          {/* Chat and Calendar Section */}
          <div className="col-span-8 border-r border-gray-700 flex flex-col">
            {showCalendar && usernames.length > 0 && (
              <div className="border-b border-gray-700 p-4 bg-gray-800">
                <CalendarView
                  username={usernames[0]}
                  onSlotsUpdate={setFreeSlots}
                />
              </div>
            )}
            <div className="flex-1">
              <Chat
                messages={messages}
                isLoading={isLoading}
                onSubmit={handleSendMessage}
                className="h-full"
              />
            </div>
          </div>

          {/* Recommendations and Profiles Section */}
          <div className="col-span-4 flex flex-col h-full">
            {/* Movie Recommendations */}
            {usernames.length > 0 && (
              <div className="flex-1 p-4 overflow-y-auto bg-gray-800">
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
              <div key={name} className="p-4 bg-gray-800 border-t border-gray-700">
                <LetterboxdProfile username={name} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </NavLayout>
  );
}