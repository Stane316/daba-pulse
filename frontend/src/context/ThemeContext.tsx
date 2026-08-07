import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  toggle: () => void
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeState | null>(null)

const STORAGE_KEY = 'dabapulse-theme'

function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null
    if (stored === 'dark' || stored === 'light') return stored
  } catch { /* ignore */ }
  // System preference fallback
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeRaw] = useState<Theme>(() => {
    // SSR safe: default dark, corrected in effect
    if (typeof window === 'undefined') return 'dark'
    return getInitialTheme()
  })

  const apply = useCallback((t: Theme) => {
    document.documentElement.setAttribute('data-theme', t)
    document.documentElement.style.colorScheme = t
    try {
      localStorage.setItem(STORAGE_KEY, t)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    apply(theme)
  }, [theme, apply])

  // Sync across tabs
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && (e.newValue === 'dark' || e.newValue === 'light')) {
        setThemeRaw(e.newValue)
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const setTheme = useCallback((t: Theme) => {
    setThemeRaw(t)
    apply(t)
  }, [apply])

  const toggle = useCallback(() => {
    setThemeRaw((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark'
      apply(next)
      return next
    })
  }, [apply])

  return <ThemeContext.Provider value={{ theme, toggle, setTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
