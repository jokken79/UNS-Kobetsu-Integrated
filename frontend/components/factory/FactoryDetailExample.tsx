'use client'

import { useState } from 'react'
import { FactoryDetail } from './FactoryDetail'
import { useFactoryList } from '@/hooks/useFactories'

/**
 * Example component showing how to use FactoryDetail in a split view layout
 * This demonstrates the typical usage pattern with a factory list on the left
 * and the detail view on the right
 */
export function FactoryDetailExample() {
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(null)
  const { data: factories, isLoading } = useFactoryList()

  const handleSave = () => {
    console.log('Factory saved successfully')
    // Could trigger a refetch or update UI here
  }

  const handleDelete = () => {
    console.log('Factory deleted')
    setSelectedFactoryId(null)
    // Could navigate away or show a different view
  }

  if (isLoading) {
    return (
      <div className="flex h-screen">
        <div className="w-1/3 p-4 border-r">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
        <div className="flex-1 p-4">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-4/5"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Panel - Factory List */}
      <div className="w-1/3 bg-white border-r overflow-y-auto">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">工場一覧</h2>
        </div>
        <div className="divide-y">
          {factories?.map((factory) => (
            <button
              key={factory.id}
              onClick={() => setSelectedFactoryId(factory.id)}
              className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                selectedFactoryId === factory.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
              }`}
            >
              <div className="font-medium">{factory.company_name}</div>
              <div className="text-sm text-gray-600">{factory.plant_name}</div>
              <div className="text-xs text-gray-500 mt-1">
                ライン数: {factory.lines_count} | 従業員数: {factory.employees_count}
              </div>
            </button>
          ))}
          {(!factories || factories.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              工場が登録されていません
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Factory Detail */}
      <div className="flex-1 p-6 overflow-y-auto">
        <FactoryDetail
          factoryId={selectedFactoryId}
          onSave={handleSave}
          onDelete={handleDelete}
        />
      </div>
    </div>
  )
}

/**
 * Usage Example in a page component:
 *
 * // app/factories/[id]/page.tsx
 * 'use client'
 *
 * import { FactoryDetail } from '@/components/factory/FactoryDetail'
 * import { useRouter } from 'next/navigation'
 *
 * export default function FactoryDetailPage({ params }: { params: { id: string } }) {
 *   const router = useRouter()
 *   const factoryId = parseInt(params.id)
 *
 *   const handleSave = () => {
 *     // Could show a success message
 *   }
 *
 *   const handleDelete = () => {
 *     router.push('/factories')
 *   }
 *
 *   return (
 *     <div className="container mx-auto p-6">
 *       <FactoryDetail
 *         factoryId={factoryId}
 *         onSave={handleSave}
 *         onDelete={handleDelete}
 *       />
 *     </div>
 *   )
 * }
 */