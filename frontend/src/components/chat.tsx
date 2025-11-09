'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'
import { ChatMessage } from './chat-message'
import { Message } from '@/lib/types'

export interface ChatProps {
  messages: Message[]
  isLoading?: boolean
  onSubmit?: (value: string) => void
  onPanelToggle?: () => void
  className?: string
}

export function Chat({ messages, isLoading, onSubmit, onPanelToggle, className }: ChatProps) {
  const [input, setInput] = React.useState('')
  const inputRef = React.useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input?.trim() || isLoading) {
      return
    }
    onSubmit?.(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className={`flex flex-col h-full max-h-full ${className}`}>
      {/* Messages area - scrollable with explicit overflow handling */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-4 min-h-0">
        <div className="space-y-4 mx-auto max-w-2xl pb-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-lg mb-2">👋 Welcome to Movie Matcher!</p>
              <p className="text-sm">I can help you find movies to watch with friends based on:</p>
              <ul className="text-sm mt-4 space-y-2">
                <li>📽️ Letterboxd movie preferences</li>
                <li>📅 Calendar availability</li>
                <li>🎬 Cineville showtimes in Amsterdam</li>
              </ul>
              <p className="text-sm mt-4">Try: "Add @visionofdavinci" or "What movies are showing this week?"</p>
            </div>
          ) : (
            <>
              {messages.map((message, i) => (
                <ChatMessage 
                  key={i} 
                  message={message} 
                  onPanelToggle={onPanelToggle}
                />
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-800 rounded-lg px-4 py-2 text-gray-300">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area - fixed at bottom */}
      <div className="flex-shrink-0 border-t border-gray-700 bg-gray-900 p-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-2xl">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              tabIndex={0}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isLoading ? 'Thinking...' : 'Send a message...'}
              disabled={isLoading}
              className="min-h-[44px] max-h-32 w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement
                target.style.height = 'auto'
                target.style.height = Math.min(target.scrollHeight, 128) + 'px'
              }}
            />
            <Button 
              type="submit" 
              size="icon" 
              disabled={isLoading || !input.trim()}
              className="shrink-0 h-[44px] w-[44px]"
            >
              <Send className="h-4 w-4" />
              <span className="sr-only">Send message</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}