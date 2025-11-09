'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { Message } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Calendar, Film, Filter, Lightbulb, ChevronRight } from 'lucide-react'
import { useRouter } from 'next/navigation'

export interface ChatMessageProps {
  message: Message
  isLoading?: boolean
  className?: string
  onPanelToggle?: () => void
}

export function ChatMessage({
  message,
  isLoading,
  className,
  onPanelToggle
}: ChatMessageProps) {
  const isUser = message.role === 'user'
  const messageRef = React.useRef<HTMLDivElement>(null)
  const router = useRouter()

  const handleActionClick = (action: any) => {
    switch (action.type) {
      case 'navigation':
        if (action.data?.page) {
          router.push(action.data.page)
        }
        break
      case 'suggestion':
        // Open right panel to show recommendations
        onPanelToggle?.()
        break
      case 'filter':
        // Could trigger a filter update in parent
        console.log('Filter action:', action.data)
        break
    }
  }

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'navigation': return <Calendar className="w-4 h-4" />
      case 'suggestion': return <Film className="w-4 h-4" />
      case 'filter': return <Filter className="w-4 h-4" />
      default: return <Lightbulb className="w-4 h-4" />
    }
  }

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
        <div className="break-words whitespace-pre-wrap">
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
        
        {/* Agent Action Buttons */}
        {!isUser && message.actions && message.actions.length > 0 && (
          <div className="flex flex-col gap-2 mt-2 pt-2 border-t border-gray-700">
            {message.actions.map((action, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="justify-start gap-2 bg-gray-700/50 hover:bg-gray-600 text-white border-gray-600 text-xs"
                onClick={() => handleActionClick(action)}
              >
                {getActionIcon(action.type)}
                <span className="flex-1 text-left">{action.description}</span>
                <ChevronRight className="w-3 h-3" />
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}