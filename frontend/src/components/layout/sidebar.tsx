'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/lib/store'
import {
  LayoutDashboard, FolderGit2, MessageSquare, Share2, FileText,
  Boxes, BarChart3, Search, ListChecks, Settings, Moon, Sun, PanelLeftClose, PanelLeft,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/repositories', label: 'Repositories', icon: FolderGit2 },
  { href: '/chat', label: 'AI Chat', icon: MessageSquare },
  { href: '/graph', label: 'Knowledge Graph', icon: Share2 },
  { href: '/docs', label: 'Documentation', icon: FileText },
  { href: '/architecture', label: 'Architecture', icon: Boxes },
  { href: '/impact', label: 'Impact Analysis', icon: BarChart3 },
  { href: '/search', label: 'Search', icon: Search },
  { href: '/jobs', label: 'Jobs', icon: ListChecks },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, toggleSidebar, theme, setTheme } = useAppStore()

  return (
    <aside className={cn(
      'flex flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-300',
      sidebarOpen ? 'w-64' : 'w-16'
    )}>
      <div className="flex items-center gap-2 px-4 h-16 border-b">
        {sidebarOpen && <span className="text-lg font-bold text-primary">AutoDocOps</span>}
        <Button variant="ghost" size="icon" className="ml-auto" onClick={toggleSidebar}>
          {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
          return (
            <Link key={item.href} href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                !sidebarOpen && 'justify-center px-2'
              )}>
              <item.icon className="h-4 w-4 shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      <div className="border-t p-2">
        <Button variant="ghost" size={sidebarOpen ? 'default' : 'icon'} className="w-full" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {sidebarOpen && <span className="ml-2">{theme === 'dark' ? 'Light' : 'Dark'} Mode</span>}
        </Button>
      </div>
    </aside>
  )
}
