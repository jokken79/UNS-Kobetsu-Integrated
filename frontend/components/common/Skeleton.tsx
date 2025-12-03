'use client'

import { cn } from '@/lib/utils'

interface SkeletonBaseProps {
  className?: string
}

/**
 * Base skeleton with shimmer animation
 * The shimmer effect is a moving gradient from left to right
 */
export function SkeletonBase({ className }: SkeletonBaseProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden bg-gray-200 dark:bg-gray-700',
        'before:absolute before:inset-0',
        'before:-translate-x-full',
        'before:animate-shimmer',
        'before:bg-gradient-to-r',
        'before:from-transparent before:via-white/60 dark:before:via-white/20 before:to-transparent',
        className
      )}
    />
  )
}

interface SkeletonTextProps {
  lines?: number
  className?: string
}

/**
 * Skeleton for text content with multiple lines
 * Each line has a slightly different width for a more natural look
 */
export function SkeletonText({ lines = 3, className }: SkeletonTextProps) {
  const widths = ['w-full', 'w-11/12', 'w-4/5', 'w-3/4', 'w-2/3']

  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <SkeletonBase
          key={index}
          className={cn(
            'h-4 rounded',
            widths[index % widths.length]
          )}
        />
      ))}
    </div>
  )
}

interface SkeletonAvatarProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/**
 * Circular skeleton for avatar/profile images
 */
export function SkeletonAvatar({ size = 'md', className }: SkeletonAvatarProps) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  }

  return (
    <SkeletonBase
      className={cn(
        'rounded-full',
        sizeClasses[size],
        className
      )}
    />
  )
}

interface SkeletonCardProps {
  className?: string
}

/**
 * Full card skeleton matching the standard card layout
 */
export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 p-6', className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <SkeletonAvatar size="sm" />
          <div className="space-y-2">
            <SkeletonBase className="h-5 w-32 rounded" />
            <SkeletonBase className="h-3 w-24 rounded" />
          </div>
        </div>
        <SkeletonBase className="h-8 w-20 rounded-lg" />
      </div>

      {/* Content */}
      <SkeletonText lines={3} />

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
        <SkeletonBase className="h-4 w-24 rounded" />
        <SkeletonBase className="h-4 w-16 rounded" />
      </div>
    </div>
  )
}

interface SkeletonTableProps {
  rows?: number
  columns?: number
  showHeader?: boolean
  className?: string
}

/**
 * Table skeleton with configurable rows and columns
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  showHeader = true,
  className
}: SkeletonTableProps) {
  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 overflow-hidden', className)}>
      {showHeader && (
        <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
          <div className="flex space-x-6">
            {Array.from({ length: columns }).map((_, index) => (
              <SkeletonBase
                key={`header-${index}`}
                className="h-4 flex-1 rounded"
              />
            ))}
          </div>
        </div>
      )}

      <div className="divide-y divide-gray-200">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`row-${rowIndex}`} className="px-6 py-4">
            <div className="flex space-x-6">
              {Array.from({ length: columns }).map((_, colIndex) => {
                // Make first column slightly wider (for IDs/names)
                const width = colIndex === 0 ? 'w-32' : 'w-24'
                return (
                  <SkeletonBase
                    key={`cell-${rowIndex}-${colIndex}`}
                    className={cn('h-5 rounded', width)}
                  />
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface SkeletonStatsProps {
  count?: number
  className?: string
}

/**
 * Stats cards skeleton for dashboard statistics
 */
export function SkeletonStats({ count = 6, className }: SkeletonStatsProps) {
  return (
    <div className={cn('grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4', className)}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white rounded-xl border border-gray-200 p-5">
          {/* Icon */}
          <SkeletonBase className="w-12 h-12 rounded-xl mb-4" />

          {/* Value */}
          <SkeletonBase className="h-8 w-20 rounded mb-2" />

          {/* Label */}
          <SkeletonBase className="h-4 w-16 rounded" />
        </div>
      ))}
    </div>
  )
}

/**
 * List item skeleton for simple list layouts
 */
export function SkeletonListItem() {
  return (
    <div className="flex items-center space-x-4 py-3">
      <SkeletonAvatar size="sm" />
      <div className="flex-1 space-y-2">
        <SkeletonBase className="h-5 w-32 rounded" />
        <SkeletonBase className="h-4 w-24 rounded" />
      </div>
      <SkeletonBase className="h-8 w-16 rounded-lg" />
    </div>
  )
}

/**
 * Form field skeleton
 */
export function SkeletonFormField() {
  return (
    <div className="space-y-2">
      <SkeletonBase className="h-4 w-24 rounded" /> {/* Label */}
      <SkeletonBase className="h-10 w-full rounded-lg" /> {/* Input */}
    </div>
  )
}

/**
 * Button skeleton
 */
export function SkeletonButton({ className }: { className?: string }) {
  return (
    <SkeletonBase
      className={cn(
        'h-10 w-24 rounded-lg',
        className
      )}
    />
  )
}

/**
 * Badge skeleton
 */
export function SkeletonBadge() {
  return <SkeletonBase className="h-6 w-16 rounded-full" />
}

/**
 * Full page skeleton for initial loading states
 */
export function SkeletonPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <SkeletonBase className="h-9 w-48 rounded mb-2" />
          <SkeletonBase className="h-5 w-64 rounded" />
        </div>
        <SkeletonButton className="w-32" />
      </div>

      {/* Stats */}
      <SkeletonStats count={4} className="mb-6" />

      {/* Content */}
      <SkeletonTable rows={8} columns={5} />
    </div>
  )
}

/**
 * Detail page skeleton
 */
export function SkeletonDetail() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <SkeletonBase className="h-4 w-64 rounded mb-6" />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <SkeletonBase className="h-9 w-48 rounded" />
          <div className="flex space-x-2">
            <SkeletonButton />
            <SkeletonButton />
          </div>
        </div>
        <SkeletonText lines={2} className="max-w-2xl" />
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  )
}