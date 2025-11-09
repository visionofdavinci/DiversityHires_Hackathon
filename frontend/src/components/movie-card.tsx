import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'
import Image from 'next/image'

interface MovieCardProps {
  title: string
  year: number
  posterUrl?: string
  score: number
  onClick?: () => void
  className?: string
  showtimes?: Array<{ cinema: string; start: string }>
  userScores?: Record<string, number>
  tmdbData?: any
}

export function MovieCard({
  title,
  year,
  posterUrl,
  score,
  onClick,
  className,
  showtimes = [],
  userScores = {},
  tmdbData,
}: MovieCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        'group relative overflow-hidden rounded-lg bg-neutral-900 cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      <div className="aspect-[2/3] relative">
        {posterUrl ? (
          <Image
            src={posterUrl}
            alt={title}
            fill
            className="object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full bg-neutral-800 flex items-center justify-center">
            <span className="text-4xl text-neutral-600">🎬</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
      </div>
      <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm opacity-75">{year}</span>
            <span className="text-sm font-medium bg-white/20 px-2 py-1 rounded">
              {score.toFixed(1)}
            </span>
          </div>
          
          {userScores && Object.keys(userScores).length > 0 && (
            <div className="space-y-1 mt-1 text-xs">
              {Object.entries(userScores).map(([username, score]) => (
                <div key={username} className="flex justify-between items-center">
                  <span className="opacity-75">@{username}</span>
                  <span className="font-medium">{(score * 5).toFixed(1)}</span>
                </div>
              ))}
            </div>
          )}

          {showtimes && showtimes.length > 0 && (
            <div className="mt-1 text-xs space-y-1">
              {showtimes.slice(0, 2).map((showtime, idx) => (
                <div key={idx} className="opacity-75">
                  {new Date(showtime.start).toLocaleString()} at {showtime.cinema}
                </div>
              ))}
              {showtimes.length > 2 && (
                <div className="opacity-75">+{showtimes.length - 2} more showtimes</div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}