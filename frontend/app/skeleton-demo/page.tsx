'use client'

import { useState } from 'react'
import {
  SkeletonBase,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonTable,
  SkeletonStats,
  SkeletonListItem,
  SkeletonFormField,
  SkeletonButton,
  SkeletonBadge,
  SkeletonPage,
  SkeletonDetail
} from '@/components/common/Skeleton'

export default function SkeletonDemoPage() {
  const [showSkeletons, setShowSkeletons] = useState(true)

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Skeleton Components Demo
        </h1>
        <p className="text-gray-600 mb-4">
          Demonstration of all skeleton loader components with shimmer effect
        </p>
        <button
          onClick={() => setShowSkeletons(!showSkeletons)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showSkeletons ? 'Hide' : 'Show'} Skeletons
        </button>
      </div>

      {showSkeletons && (
        <>
          {/* SkeletonBase */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonBase</h2>
            <p className="text-gray-600 mb-4">Base skeleton with shimmer animation</p>
            <div className="space-y-3">
              <SkeletonBase className="h-4 w-full rounded" />
              <SkeletonBase className="h-10 w-64 rounded-lg" />
              <SkeletonBase className="h-20 w-full rounded-xl" />
            </div>
          </section>

          {/* SkeletonText */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonText</h2>
            <p className="text-gray-600 mb-4">Multiple lines of text with varying widths</p>
            <div className="space-y-6">
              <div>
                <p className="text-sm text-gray-500 mb-2">3 lines (default)</p>
                <SkeletonText />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">5 lines</p>
                <SkeletonText lines={5} />
              </div>
            </div>
          </section>

          {/* SkeletonAvatar */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonAvatar</h2>
            <p className="text-gray-600 mb-4">Circular avatar in different sizes</p>
            <div className="flex items-center space-x-4">
              <div>
                <p className="text-sm text-gray-500 mb-2">Small</p>
                <SkeletonAvatar size="sm" />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Medium</p>
                <SkeletonAvatar size="md" />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Large</p>
                <SkeletonAvatar size="lg" />
              </div>
            </div>
          </section>

          {/* SkeletonCard */}
          <section className="bg-gray-50 rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonCard</h2>
            <p className="text-gray-600 mb-4">Full card skeleton with header, content, and footer</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          </section>

          {/* SkeletonTable */}
          <section className="bg-gray-50 rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonTable</h2>
            <p className="text-gray-600 mb-4">Table with configurable rows and columns</p>
            <div className="space-y-6">
              <div>
                <p className="text-sm text-gray-500 mb-2">5 rows, 4 columns (default)</p>
                <SkeletonTable />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">3 rows, 6 columns, no header</p>
                <SkeletonTable rows={3} columns={6} showHeader={false} />
              </div>
            </div>
          </section>

          {/* SkeletonStats */}
          <section className="bg-gray-50 rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonStats</h2>
            <p className="text-gray-600 mb-4">Statistics cards for dashboards</p>
            <div className="space-y-6">
              <div>
                <p className="text-sm text-gray-500 mb-2">6 stats (default)</p>
                <SkeletonStats />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">4 stats</p>
                <SkeletonStats count={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4" />
              </div>
            </div>
          </section>

          {/* SkeletonListItem */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">SkeletonListItem</h2>
            <p className="text-gray-600 mb-4">List items with avatar and action</p>
            <div className="divide-y divide-gray-200">
              <SkeletonListItem />
              <SkeletonListItem />
              <SkeletonListItem />
            </div>
          </section>

          {/* Form Elements */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Form Elements</h2>
            <p className="text-gray-600 mb-4">Form fields, buttons, and badges</p>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SkeletonFormField />
                <SkeletonFormField />
              </div>
              <div className="flex items-center space-x-4">
                <SkeletonButton />
                <SkeletonButton className="w-32" />
                <SkeletonButton className="w-40" />
              </div>
              <div className="flex items-center space-x-2">
                <SkeletonBadge />
                <SkeletonBadge />
                <SkeletonBadge />
              </div>
            </div>
          </section>

          {/* Full Page Skeletons */}
          <section className="space-y-8">
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">SkeletonPage</h2>
              <p className="text-gray-600 mb-4">Full page skeleton for initial loading</p>
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <SkeletonPage />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">SkeletonDetail</h2>
              <p className="text-gray-600 mb-4">Detail page skeleton</p>
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <SkeletonDetail />
              </div>
            </div>
          </section>

          {/* Animation Timing Demo */}
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Shimmer Animation</h2>
            <p className="text-gray-600 mb-4">
              The shimmer effect moves from left to right with a 2-second duration
            </p>
            <div className="space-y-3">
              <div className="relative">
                <p className="text-sm text-gray-500 mb-2">Watch the shimmer effect:</p>
                <SkeletonBase className="h-16 w-full rounded-lg" />
              </div>
              <div className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg">
                <p className="font-semibold mb-2">Animation Details:</p>
                <ul className="space-y-1">
                  <li>• Duration: 2 seconds</li>
                  <li>• Timing: Linear</li>
                  <li>• Direction: Left to right</li>
                  <li>• Gradient: Transparent → White/60% → Transparent</li>
                  <li>• Dark mode ready with reduced opacity</li>
                </ul>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}