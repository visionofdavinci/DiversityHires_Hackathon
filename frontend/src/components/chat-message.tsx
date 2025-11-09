'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { Message } from '@/lib/types'

export interface ChatMessageProps {
  message: Message
  isLoading?: boolean
  className?: string
}

export function ChatMessage({
  message,
  isLoading,
  className,
}: ChatMessageProps) {
  const isUser = message.role === 'user'
  const messageRef = React.useRef<HTMLDivElement>(null)

  return (
    <div
      ref={messageRef}
      className={cn(
        'group relative mb-4 flex items-start md:mb-6',
        isUser ? 'justify-end' : 'justify-start',
        className
      )}
    >
      <div
        className={cn(
          'flex max-w-[85%] flex-col gap-2 rounded-lg px-4 py-3 sm:max-w-[75%]',
          isUser
            ? 'bg-gray-700 text-white'
            : 'bg-gray-800 text-white'
        )}
      >
        <div className="break-words">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:-0.3s]"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:-0.15s]"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-current"></div>
            </div>
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  )
}