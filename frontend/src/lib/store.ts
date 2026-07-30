import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  activeRepoId: number | null
  toggleSidebar: () => void
  setTheme: (t: 'light' | 'dark') => void
  setActiveRepo: (id: number | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  activeRepoId: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', theme === 'dark')
    }
    set({ theme })
  },
  setActiveRepo: (activeRepoId) => set({ activeRepoId }),
}))
