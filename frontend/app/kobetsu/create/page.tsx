'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { kobetsuApi } from '@/lib/api'
import type { KobetsuCreate } from '@/types'
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'
import { RateGroupPreview } from '@/components/kobetsu/RateGroupPreview'
import { useToastActions } from '@/components/common/ToastContext'

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
  const toast = useToastActions()
  const [error, setError] = useState<string | null>(null)

  // Rate group preview states
  const [showRatePreview, setShowRatePreview] = useState(false)
  const [rateGroups, setRateGroups] = useState<any>(null)
  const [isCheckingRates, setIsCheckingRates] = useState(false)
  const [pendingFormData, setPendingFormData] = useState<KobetsuCreate | null>(null)

  const createMutation = useMutation({
    mutationFn: (data: KobetsuCreate) => kobetsuApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-stats'] })
      toast.success('契約書を作成しました')
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

  const batchCreateMutation = useMutation({
    mutationFn: (data: {
      factory_id: number
      base_contract_data: Partial<KobetsuCreate>
      groups: Array<{
        employee_ids: number[]
        hourly_rate: number
        billing_rate?: number
      }>
    }) => kobetsuApi.batchCreate(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-stats'] })
      toast.success(`${result.contracts_created}件の契約書を作成しました`)

      // Navigate to the list page instead of a specific contract
      router.push('/kobetsu')
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error('複数契約の作成に失敗しました')
      }
    },
  })

  const handleSubmit = async (data: KobetsuCreate) => {
    setError(null)
    setPendingFormData(data)

    // If there are multiple employees, check if they have different rates
    if (data.employee_ids && data.employee_ids.length > 1) {
      setIsCheckingRates(true)
      try {
        const groupResult = await kobetsuApi.groupByRate(data.employee_ids)

        if (groupResult.has_multiple_rates) {
          // Show the rate preview dialog
          setRateGroups(groupResult)
          setShowRatePreview(true)
        } else {
          // All employees have the same rate, create single contract
          createMutation.mutate(data)
        }
      } catch (error) {
        console.error('Failed to check employee rates:', error)
        toast.error('従業員の時給確認に失敗しました')
        // Fall back to single contract creation
        createMutation.mutate(data)
      } finally {
        setIsCheckingRates(false)
      }
    } else {
      // Single employee or no employees, create single contract
      createMutation.mutate(data)
    }
  }

  const handleRatePreviewConfirm = async (splitByRate: boolean) => {
    setShowRatePreview(false)

    if (!pendingFormData || !rateGroups) {
      toast.error('フォームデータが見つかりません')
      return
    }

    if (splitByRate) {
      // Create multiple contracts via batch API
      const batchData = {
        factory_id: pendingFormData.factory_id,
        base_contract_data: {
          ...pendingFormData,
          employee_ids: undefined, // Remove employee_ids from base data
        },
        groups: rateGroups.groups.map((group: any) => ({
          employee_ids: group.employees.map((e: any) => e.id),
          hourly_rate: group.hourly_rate,
          billing_rate: group.billing_rate,
        })),
      }

      batchCreateMutation.mutate(batchData)
    } else {
      // Create single contract with uniform rate (use the form's hourly rate)
      createMutation.mutate(pendingFormData)
    }
  }

  const handleRatePreviewCancel = () => {
    setShowRatePreview(false)
    setRateGroups(null)
    setPendingFormData(null)
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          dashboardBreadcrumb,
          { label: '個別契約書', href: '/kobetsu' },
          { label: '新規作成' }
        ]}
        className="mb-4"
      />

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
            isLoading={createMutation.isPending || batchCreateMutation.isPending || isCheckingRates}
          />
        </div>
      </div>

      {/* Rate Group Preview Modal */}
      {showRatePreview && rateGroups && (
        <RateGroupPreview
          groups={rateGroups.groups}
          totalEmployees={rateGroups.total_employees}
          hasMultipleRates={rateGroups.has_multiple_rates}
          suggestedContracts={rateGroups.suggested_contracts}
          message={rateGroups.message}
          onConfirm={handleRatePreviewConfirm}
          onCancel={handleRatePreviewCancel}
          isLoading={createMutation.isPending || batchCreateMutation.isPending}
        />
      )}
    </div>
  )
}
