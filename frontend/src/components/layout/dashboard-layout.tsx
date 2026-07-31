'use client'
import { usePathname } from 'next/navigation'
import { Sidebar } from './sidebar'
import { ErrorBoundary } from '@/components/error-boundary'

const publicPaths = ['/login', '/signup']

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isPublicPath = publicPaths.includes(pathname)

  if (isPublicPath) {
    return (
      <main className="flex-1 overflow-y-auto">
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>
    </div>
  )
}
