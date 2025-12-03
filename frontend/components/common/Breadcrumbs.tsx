'use client'

import Link from 'next/link'
import { HomeIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

export interface BreadcrumbItem {
  label: string
  href?: string  // if undefined, it's the current page (not clickable)
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className = '' }: BreadcrumbsProps) {
  return (
    <nav className={`flex items-center text-sm ${className}`} aria-label="Breadcrumb">
      {items.map((item, index) => (
        <div key={index} className="flex items-center">
          {index > 0 && (
            <ChevronRightIcon className="h-4 w-4 text-gray-400 mx-2" aria-hidden="true" />
          )}

          {index === 0 && item.href ? (
            // First item with home icon (if it has href)
            <Link
              href={item.href}
              className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
            >
              <HomeIcon className="h-4 w-4 mr-1" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          ) : index === 0 ? (
            // First item without href (current page)
            <div className="flex items-center text-gray-900">
              <HomeIcon className="h-4 w-4 mr-1" aria-hidden="true" />
              <span>{item.label}</span>
            </div>
          ) : item.href ? (
            // Other items with href (clickable)
            <Link
              href={item.href}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            // Current page (no href)
            <span className="text-gray-900" aria-current="page">
              {item.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  )
}

// Export a default breadcrumb item for dashboard/home
export const dashboardBreadcrumb: BreadcrumbItem = {
  label: 'ダッシュボード',
  href: '/'
}