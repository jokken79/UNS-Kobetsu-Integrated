'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'

// SVG Icons as components for better styling
const Icons = {
  Dashboard: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  ),
  Document: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Users: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  Plus: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  ),
  Import: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  ),
  Building: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
    </svg>
  ),
  Settings: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c-.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Menu: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  ),
  Close: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  ChevronLeft: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  ),
  ChevronRight: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  ),
}

const navigation = [
  {
    name: 'ダッシュボード',
    href: '/',
    icon: Icons.Dashboard,
    description: '概要を確認',
  },
  {
    name: '個別契約書',
    href: '/kobetsu',
    icon: Icons.Document,
    description: '契約書一覧',
  },
  {
    name: '従業員管理',
    href: '/employees',
    icon: Icons.Users,
    description: '従業員一覧',
  },
  {
    name: '派遣先企業',
    href: '/factories',
    icon: Icons.Building,
    description: '企業・工場一覧',
  },
  {
    name: '従業員配属',
    href: '/assign',
    icon: Icons.Users,
    description: '配属管理',
  },
  {
    name: '新規契約作成',
    href: '/kobetsu/create',
    icon: Icons.Plus,
    description: '契約書を作成',
  },
  {
    name: 'データインポート',
    href: '/import',
    icon: Icons.Import,
    description: 'Excel/JSON取込',
  },
  {
    name: 'システム設定',
    href: '/settings',
    icon: Icons.Settings,
    description: 'UNS企画デフォルト設定',
  },
]

export function SidebarClient() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const NavContent = () => (
    <>
      {/* Logo */}
      <div className="px-6 py-6 border-b border-gray-200">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-10 h-10 rounded-lg bg-theme-600
                          flex items-center justify-center
                          hover:bg-theme-700 transition-colors duration-200">
            <span className="text-white font-bold text-lg">U</span>
          </div>
          {!collapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-bold text-gray-900 tracking-tight">UNS Kobetsu</h1>
              <p className="text-xs text-gray-500">個別契約書管理システム</p>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 overflow-y-auto scrollbar-thin">
        {!collapsed && (
          <div className="px-3 mb-3">
            <span className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              メインメニュー
            </span>
          </div>
        )}
        <ul className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))

            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`group relative flex items-center gap-3 px-3 py-2 mx-2 rounded-lg
                            transition-all duration-150 ${
                    isActive
                      ? 'bg-theme-50 text-theme-600 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                  title={collapsed ? item.name : undefined}
                >
                  <span className="flex-shrink-0">
                    <Icon />
                  </span>
                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <span className="block font-medium truncate text-sm">{item.name}</span>
                      <span className={`block text-xs truncate transition-colors ${
                        isActive ? 'text-theme-500' : 'text-gray-400'
                      }`}>
                        {item.description}
                      </span>
                    </div>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>

        {/* Quick Stats - Clean Design */}
        {!collapsed && (
          <div className="px-5 mt-8">
            <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-md bg-theme-600 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <span className="text-sm font-semibold text-gray-900">クイック情報</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-white p-3 rounded-md border border-gray-200">
                  <p className="text-2xl font-bold text-gray-900 mb-1">--</p>
                  <p className="text-xs text-gray-500">有効契約</p>
                </div>
                <div className="bg-white p-3 rounded-md border border-gray-200">
                  <p className="text-2xl font-bold text-amber-600 mb-1">--</p>
                  <p className="text-xs text-gray-500">期限間近</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-md bg-gray-200
                          flex items-center justify-center flex-shrink-0 text-gray-600">
            <Icons.Building />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">株式会社UNS企画</p>
              <p className="text-xs text-gray-500">派13-123456</p>
            </div>
          )}
        </div>
      </div>

      {/* Collapse Toggle - Desktop Only */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="hidden lg:flex absolute -right-3 top-20 w-6 h-6 bg-white border border-gray-300
                 rounded-full items-center justify-center text-gray-600 hover:bg-gray-50
                 transition-all duration-200 shadow-sm z-50 group"
        aria-label={collapsed ? "サイドバーを展開" : "サイドバーを折りたたむ"}
      >
        {collapsed ? <Icons.ChevronRight /> : <Icons.ChevronLeft />}
      </button>
    </>
  )

  if (!mounted) {
    return null // Avoid rendering until mounted
  }

  // Don't render sidebar on login page
  if (pathname === '/login') {
    return null
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-50 p-2 rounded-xl bg-white shadow-lg border border-gray-200
                   lg:hidden hover:bg-gray-50 transition-all duration-300 hover:scale-105"
        aria-label="メニューを開く"
      >
        <Icons.Menu />
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-screen w-72 bg-white border-r border-gray-200
                    flex flex-col z-50 shadow-lg transform transition-transform duration-300
                    lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600"
          aria-label="メニューを閉じる"
        >
          <Icons.Close />
        </button>
        <NavContent />
      </aside>

      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:flex sidebar transition-all duration-300 ${collapsed ? 'w-20' : 'w-72'}`}
      >
        <NavContent />
      </aside>
    </>
  )
}
