'use client'

import { useState, useEffect } from 'react'

// Define 5 beautiful color themes
export const themes = {
  blue: {
    name: 'Ocean Blue',
    primary: 'blue',
    colors: {
      50: 'bg-blue-50',
      100: 'bg-blue-100',
      200: 'bg-blue-200',
      500: 'bg-blue-500',
      600: 'bg-blue-600',
      700: 'bg-blue-700',
      text: 'text-blue-600',
      border: 'border-blue-200',
      ring: 'ring-blue-500',
    }
  },
  purple: {
    name: 'Royal Purple',
    primary: 'purple',
    colors: {
      50: 'bg-purple-50',
      100: 'bg-purple-100',
      200: 'bg-purple-200',
      500: 'bg-purple-500',
      600: 'bg-purple-600',
      700: 'bg-purple-700',
      text: 'text-purple-600',
      border: 'border-purple-200',
      ring: 'ring-purple-500',
    }
  },
  green: {
    name: 'Forest Green',
    primary: 'emerald',
    colors: {
      50: 'bg-emerald-50',
      100: 'bg-emerald-100',
      200: 'bg-emerald-200',
      500: 'bg-emerald-500',
      600: 'bg-emerald-600',
      700: 'bg-emerald-700',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
      ring: 'ring-emerald-500',
    }
  },
  orange: {
    name: 'Sunset Orange',
    primary: 'orange',
    colors: {
      50: 'bg-orange-50',
      100: 'bg-orange-100',
      200: 'bg-orange-200',
      500: 'bg-orange-500',
      600: 'bg-orange-600',
      700: 'bg-orange-700',
      text: 'text-orange-600',
      border: 'border-orange-200',
      ring: 'ring-orange-500',
    }
  },
  rose: {
    name: 'Cherry Blossom',
    primary: 'rose',
    colors: {
      50: 'bg-rose-50',
      100: 'bg-rose-100',
      200: 'bg-rose-200',
      500: 'bg-rose-500',
      600: 'bg-rose-600',
      700: 'bg-rose-700',
      text: 'text-rose-600',
      border: 'border-rose-200',
      ring: 'ring-rose-500',
    }
  }
}

export type ThemeKey = keyof typeof themes
export type ThemeMode = 'light' | 'dark' | 'system'

// Theme preview colors for the selector
const themePreviewColors: Record<ThemeKey, string> = {
  blue: 'bg-blue-600',
  purple: 'bg-purple-600',
  green: 'bg-emerald-600',
  orange: 'bg-orange-600',
  rose: 'bg-rose-600',
}

export function ThemeSwitcher() {
  const [currentTheme, setCurrentTheme] = useState<ThemeKey>('blue')
  const [currentMode, setCurrentMode] = useState<ThemeMode>('light')
  const [isOpen, setIsOpen] = useState(false)

  // Load theme and mode from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as ThemeKey
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode

    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme)
      applyTheme(savedTheme)
    }

    if (savedMode) {
      setCurrentMode(savedMode)
      applyMode(savedMode)
    } else {
      // Default to light mode
      applyMode('light')
    }
  }, [])

  const applyMode = (mode: ThemeMode) => {
    localStorage.setItem('theme-mode', mode)

    if (mode === 'dark') {
      document.documentElement.classList.add('dark')
    } else if (mode === 'light') {
      document.documentElement.classList.remove('dark')
    } else {
      // System preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }

    setCurrentMode(mode)
  }

  const applyTheme = (theme: ThemeKey) => {
    // Store in localStorage
    localStorage.setItem('theme', theme)

    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)

    setCurrentTheme(theme)
  }

  const handleThemeChange = (theme: ThemeKey) => {
    applyTheme(theme)
    setIsOpen(false)
  }

  const handleModeToggle = () => {
    const nextMode = currentMode === 'light' ? 'dark' : 'light'
    applyMode(nextMode)
  }

  return (
    <div className="relative flex items-center gap-1">
      {/* Dark/Light Mode Toggle */}
      <button
        onClick={handleModeToggle}
        className="p-2.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
        title={currentMode === 'dark' ? 'ライトモードに切り替え' : 'ダークモードに切り替え'}
      >
        {currentMode === 'dark' ? (
          // Sun icon for light mode
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
          </svg>
        ) : (
          // Moon icon for dark mode
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
          </svg>
        )}
      </button>

      {/* Color Theme Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
        title="カラーテーマを変更"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      </button>

      {/* Theme Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Menu */}
          <div className="absolute top-full right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-lg z-50 animate-slide-down max-h-[400px] overflow-y-auto">
            <div className="p-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">カラーテーマを選択</h3>
              <div className="space-y-2">
                {(Object.keys(themes) as ThemeKey[]).map((themeKey) => {
                  const theme = themes[themeKey]
                  const isActive = currentTheme === themeKey

                  return (
                    <button
                      key={themeKey}
                      onClick={() => handleThemeChange(themeKey)}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                        isActive
                          ? 'bg-gray-100 dark:bg-gray-700 ring-2 ring-gray-300 dark:ring-gray-600'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}
                    >
                      {/* Color Preview */}
                      <div className={`w-8 h-8 rounded-lg ${themePreviewColors[themeKey]} flex items-center justify-center flex-shrink-0`}>
                        {isActive && (
                          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>

                      {/* Theme Name */}
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{theme.name}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// Hook to get current theme
export function useTheme() {
  const [theme, setTheme] = useState<ThemeKey>('blue')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as ThemeKey
    if (savedTheme && themes[savedTheme]) {
      setTheme(savedTheme)
    }

    // Listen for theme changes
    const handleThemeChange = () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') as ThemeKey
      if (currentTheme) {
        setTheme(currentTheme)
      }
    }

    const observer = new MutationObserver(handleThemeChange)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    })

    return () => observer.disconnect()
  }, [])

  return theme
}
