'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { kobetsuApi } from '@/lib/api'
import type { KobetsuCreate } from '@/types'

// Lazy load the heavy form component
const KobetsuFormHybrid = dynamic(() => import('@/components/kobetsu/KobetsuFormHybrid').then(mod => mod.KobetsuFormHybrid), {
  loading: () => (
    <div className="p-8 text-center">
      <div className="spinner w-8 h-8 mx-auto mb-4"></div>
      <p className="text-gray-500">フォームを読み込み中...</p>
    </div>
  ),
  ssr: false, // Disable SSR for form to avoid hydration issues
})

export default function CreateKobetsuPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (data: KobetsuCreate) => kobetsuApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-stats'] })
      router.push(`/kobetsu/${data.id}`)
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        // FastAPI validation errors are arrays of {type, loc, msg, input, ctx}
        const messages = detail.map((err: any) => {
          const field = err.loc?.slice(1).join('.') || 'Unknown'
          return `${field}: ${err.msg}`
        }).join('\n')
        setError(messages || 'バリデーションエラーが発生しました')
      } else if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('エラーが発生しました')
      }
    },
  })

  const handleSubmit = (data: KobetsuCreate) => {
    setError(null)
    createMutation.mutate(data)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            新規個別契約書作成
          </h1>
          <p className="text-gray-500 mt-1">
            労働者派遣法第26条に準拠した個別契約書を作成
          </p>
        </div>
        <Link href="/kobetsu" className="btn-secondary">
          ← 一覧に戻る
        </Link>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md whitespace-pre-line">
          {error}
        </div>
      )}

      {/* Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">
            契約情報入力
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            * は必須項目です
          </p>
        </div>
        <div className="card-body">
          <KobetsuFormHybrid
            onSubmit={handleSubmit}
            isLoading={createMutation.isPending}
          />
        </div>
      </div>
    </div>
  )
}
