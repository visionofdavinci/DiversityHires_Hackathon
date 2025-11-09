'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

export function NavLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  const navItems = [
    { name: 'Chat', href: '/' },
    { name: 'Letterboxd', href: '/letterboxd' },
    { name: 'Cineville', href: '/cineville' },
    { name: 'Calendar', href: '/calendar' }
  ]

  return (
    <main className="flex min-h-screen flex-col bg-gray-900">
      <div className="flex h-screen">
        {/* Navigation Menu */}
        <nav className="w-64 bg-gray-800 text-white p-6">
          <div className="space-y-6">
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Menu</h2>
              <ul className="space-y-3">
                {navItems.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        'block p-2 rounded cursor-pointer transition-colors',
                        pathname === item.href
                          ? 'bg-gray-700 text-white'
                          : 'hover:bg-gray-700'
                      )}
                    >
                      {item.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    </main>
  )
}