'use client'

import { useState, useRef, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import Link from 'next/link'
import { ThemeSwitcher } from './ThemeSwitcher'

// SVG Icons
const Icons = {
  Search: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
    </svg>
  ),
  Bell: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  ),
  ChevronDown: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  ),
  User: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  ),
  Settings: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Logout: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
    </svg>
  ),
  Help: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
    </svg>
  ),
}

export function Header() {
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Don't render header on login page
  if (pathname === '/login') {
    return null
  }

  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-b border-gray-200/40 dark:border-slate-700/40 shadow-sm">
      <div className="px-4 lg:px-6 py-3.5">
        <div className="flex justify-between items-center gap-4">
          {/* Search */}
          <div className="flex-1 max-w-xl hidden md:block">
            <div className={`relative transition-all duration-200 ${searchFocused ? 'scale-[1.02]' : ''}`}>
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 dark:text-slate-400">
                <Icons.Search />
              </div>
              <input
                type="search"
                placeholder="契約書を検索... (契約番号、派遣先など)"
                className={`w-full pl-10 pr-20 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl
                          text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-400 font-medium
                          focus:bg-white dark:focus:bg-slate-700 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-4 focus:ring-blue-500/10
                          transition-all duration-200 hover:border-gray-300 dark:hover:border-slate-600`}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
              />
              <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                <kbd className="hidden sm:inline-flex px-2 py-0.5 text-xs font-medium text-gray-400 dark:text-slate-400 bg-gray-100 dark:bg-slate-700 rounded">
                  ⌘K
                </kbd>
              </div>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* Theme Switcher */}
            <ThemeSwitcher />

            {/* Help */}
            <button
              className="p-2.5 text-gray-500 hover:text-gray-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              title="ヘルプ"
            >
              <Icons.Help />
            </button>

            {/* Notifications */}
            <button
              className="relative p-2.5 text-gray-500 hover:text-gray-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              title="通知"
            >
              <Icons.Bell />
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full
                             border-2 border-white dark:border-slate-900 animate-pulse" />
            </button>

            {/* Divider */}
            <div className="w-px h-8 bg-gray-200 dark:bg-slate-700 mx-2 hidden sm:block" />

            {/* User Menu */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className={`flex items-center gap-3 p-1.5 pr-3 rounded-xl transition-all duration-200
                          ${showDropdown ? 'bg-gray-100 dark:bg-slate-800' : 'hover:bg-gray-100 dark:hover:bg-slate-800'}`}
              >
                {/* Avatar */}
                <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-blue-600 to-violet-600
                              flex items-center justify-center text-white font-bold text-sm
                              shadow-lg shadow-blue-500/30 group-hover:shadow-blue-500/40
                              transition-all duration-300">
                  {user?.full_name?.[0] || 'U'}
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/20 to-transparent
                              opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* Name - hidden on mobile */}
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-gray-900 dark:text-white leading-tight">
                    {user?.full_name || 'ユーザー'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-slate-400 leading-tight">
                    管理者
                  </p>
                </div>

                <span className={`text-gray-400 dark:text-slate-400 transition-transform duration-200 hidden sm:block
                                ${showDropdown ? 'rotate-180' : ''}`}>
                  <Icons.ChevronDown />
                </span>
              </button>

              {/* Dropdown Menu */}
              {showDropdown && (
                <div className="dropdown right-0 mt-2 w-56 animate-slide-down bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg shadow-lg">
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-700">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {user?.full_name || 'ユーザー'}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-slate-400 truncate">
                      {user?.email || 'user@example.com'}
                    </p>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1.5">
                    <Link
                      href="/profile"
                      className="dropdown-item text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700"
                      onClick={() => setShowDropdown(false)}
                    >
                      <Icons.User />
                      <span>プロフィール</span>
                    </Link>
                    <Link
                      href="/settings"
                      className="dropdown-item text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700"
                      onClick={() => setShowDropdown(false)}
                    >
                      <Icons.Settings />
                      <span>設定</span>
                    </Link>
                  </div>

                  <div className="dropdown-divider dark:bg-slate-700" />

                  {/* Logout */}
                  <div className="py-1.5">
                    <button
                      onClick={() => {
                        logout()
                        setShowDropdown(false)
                      }}
                      className="dropdown-item w-full text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <Icons.Logout />
                      <span>ログアウト</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
