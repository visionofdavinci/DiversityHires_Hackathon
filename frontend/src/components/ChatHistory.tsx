'use client'

import { useState, useEffect } from 'react'
import { Message } from '@/lib/types'
import { X, Clock, Trash2 } from 'lucide-react'

interface ChatSession {
  id: string
  timestamp: string
  messages: Message[]
  preview: string
}

interface ChatHistoryProps {
  isOpen: boolean
  onClose: () => void
  onLoadSession: (messages: Message[]) => void
}

export function ChatHistory({ isOpen, onClose, onLoadSession }: ChatHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])

  // Load chat history from localStorage
  useEffect(() => {
    if (isOpen) {
      loadChatHistory()
    }
  }, [isOpen])

  const loadChatHistory = () => {
    const history = localStorage.getItem('movieMatcher_chatHistory')
    if (history) {
      try {
        const parsed = JSON.parse(history)
        setSessions(parsed)
      } catch (e) {
        console.error('Failed to parse chat history', e)
        setSessions([])
      }
    }
  }

  const handleLoadSession = (session: ChatSession) => {
    onLoadSession(session.messages)
    onClose()
  }

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const updatedSessions = sessions.filter(s => s.id !== sessionId)
    setSessions(updatedSessions)
    localStorage.setItem('movieMatcher_chatHistory', JSON.stringify(updatedSessions))
  }

  const handleClearAll = () => {
    if (confirm('Are you sure you want to clear all chat history?')) {
      setSessions([])
      localStorage.removeItem('movieMatcher_chatHistory')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Chat History
          </h2>
          <div className="flex gap-2">
            {sessions.length > 0 && (
              <button
                onClick={handleClearAll}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm flex items-center gap-1"
              >
                <Trash2 className="w-3 h-3" />
                Clear All
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4">
          {sessions.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No chat history yet</p>
              <p className="text-sm mt-1">Your conversations will appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleLoadSession(session)}
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 cursor-pointer transition-colors group"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <p className="text-white font-medium line-clamp-1">
                        {session.preview}
                      </p>
                      <p className="text-gray-400 text-sm">
                        {new Date(session.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-opacity ml-2"
                      title="Delete session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-gray-400 text-sm">
                    {session.messages.length} messages
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
