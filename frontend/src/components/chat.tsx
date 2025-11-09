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
  className?: string
}

export function Chat({ messages, isLoading, onSubmit, className }: ChatProps) {
  const [input, setInput] = React.useState('')
  const inputRef = React.useRef<HTMLTextAreaElement>(null)

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
    <div className={className}>
      <div className="space-y-4 mx-auto max-w-2xl px-4 pt-4 mb-32">
        {messages.map((message, i) => (
          <ChatMessage key={i} message={message} />
        ))}
      </div>
      <form
        onSubmit={handleSubmit}
        className="fixed bottom-32 inset-x-0 bg-gradient-to-b from-transparent to-gray-900 p-4"
      >
        <div className="mx-auto max-w-2xl flex items-center gap-2">
          <textarea
            ref={inputRef}
            tabIndex={0}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isLoading ? 'Thinking...' : 'Send a message...'}
            className="min-h-[44px] w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-sm text-white focus:border-gray-500 focus:outline-none focus:ring-0 placeholder-gray-400"
            style={{
              resize: 'none',
            }}
          />
          <Button type="submit" size="icon" disabled={isLoading}>
            <Send className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </form>
    </div>
  )
}