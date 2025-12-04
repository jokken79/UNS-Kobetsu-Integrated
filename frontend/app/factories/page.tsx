'use client'

import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { useConfirmActions } from '@/components/common/ConfirmContext'
import { SkeletonCard } from '@/components/common/Skeleton'
import { useToastActions } from '@/components/common/ToastContext'
import { FactoryTree } from '@/components/factory/FactoryTree'
import { LineCard } from '@/components/factory/LineCard'
import { useDeleteFactory, useUpdateFactory } from '@/hooks/useFactories'
import { employeeApi, factoryApi } from '@/lib/api'
import { formatBreakTimeForDisplay } from '@/lib/formatBreakTime'
import type {
  EmployeeResponse,
  FactoryLineResponse,
  FactoryUpdate
} from '@/types'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'

export default function FactoriesPage() {
  const router = useRouter()
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(null)
  const [isEditingFactory, setIsEditingFactory] = useState(false)
  const [factoryFormData, setFactoryFormData] = useState<FactoryUpdate>({})
  const [expandedLines, setExpandedLines] = useState<Set<number>>(new Set())

  const toast = useToastActions()
  const { confirmDelete } = useConfirmActions()

  // Fetch all factories for tree
  const { data: factories = [], isLoading: isLoadingFactories } = useQuery({
    queryKey: ['factories', 'list'],
    queryFn: () => factoryApi.getList({ limit: 500 }),
    staleTime: 5 * 60 * 1000,
  })

  // Fetch selected factory details
  const { data: factoryDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['factories', selectedFactoryId],
    queryFn: () => selectedFactoryId ? factoryApi.getById(selectedFactoryId) : null,
    enabled: !!selectedFactoryId,
  })

  // Fetch employees for the selected factory
  const { data: employees = [], isLoading: isLoadingEmployees } = useQuery({
    queryKey: ['employees', 'by-factory', selectedFactoryId],
    queryFn: () => selectedFactoryId ? employeeApi.getList({ factory_id: selectedFactoryId, limit: 500 }) : [],
    enabled: !!selectedFactoryId,
  })

  // Group employees by factory_line_id
  const employeesByLine = useMemo(() => {
    const grouped = new Map<number | null, EmployeeResponse[]>()
    employees.forEach(emp => {
      // Cast EmployeeListItem to EmployeeResponse for LineCard compatibility
      const empAsResponse = emp as unknown as EmployeeResponse
      const lineId = (emp as any).factory_line_id || null
      const existing = grouped.get(lineId) || []
      grouped.set(lineId, [...existing, empAsResponse])
    })
    return grouped
  }, [employees])

  // Mutations
  const updateFactoryMutation = useUpdateFactory(selectedFactoryId!)
  const deleteFactoryMutation = useDeleteFactory()

  // Initialize form data when factory detail loads
  useEffect(() => {
    if (factoryDetail) {
      setFactoryFormData({
        company_name: factoryDetail.company_name,
        company_address: factoryDetail.company_address,
        company_phone: factoryDetail.company_phone,
        plant_name: factoryDetail.plant_name,
        plant_address: factoryDetail.plant_address,
        plant_phone: factoryDetail.plant_phone,
        client_responsible_department: factoryDetail.client_responsible_department,
        client_responsible_name: factoryDetail.client_responsible_name,
        client_responsible_phone: factoryDetail.client_responsible_phone,
        client_complaint_department: factoryDetail.client_complaint_department,
        client_complaint_name: factoryDetail.client_complaint_name,
        client_complaint_phone: factoryDetail.client_complaint_phone,
        conflict_date: factoryDetail.conflict_date,
        break_minutes: factoryDetail.break_minutes,
      })
    }
  }, [factoryDetail])

  // Auto-select first factory on load (optional)
  useEffect(() => {
    if (!selectedFactoryId && factories.length > 0) {
      setSelectedFactoryId(factories[0].id)
    }
  }, [factories, selectedFactoryId])

  const handleSelectFactory = (factoryId: number) => {
    setSelectedFactoryId(factoryId)
    setIsEditingFactory(false)
    setExpandedLines(new Set()) // Reset expanded lines
  }

  const handleCreateNew = () => {
    router.push('/factories/create')
  }

  const handleEditFactory = () => {
    setIsEditingFactory(true)
  }

  const handleCancelEditFactory = () => {
    setIsEditingFactory(false)
    // Reset form to original data
    if (factoryDetail) {
      setFactoryFormData({
        company_name: factoryDetail.company_name,
        company_address: factoryDetail.company_address,
        company_phone: factoryDetail.company_phone,
        plant_name: factoryDetail.plant_name,
        plant_address: factoryDetail.plant_address,
        plant_phone: factoryDetail.plant_phone,
        client_responsible_department: factoryDetail.client_responsible_department,
        client_responsible_name: factoryDetail.client_responsible_name,
        client_responsible_phone: factoryDetail.client_responsible_phone,
        client_complaint_department: factoryDetail.client_complaint_department,
        client_complaint_name: factoryDetail.client_complaint_name,
        client_complaint_phone: factoryDetail.client_complaint_phone,
        conflict_date: factoryDetail.conflict_date,
        break_minutes: factoryDetail.break_minutes,
      })
    }
  }

  const handleSaveFactory = async () => {
    if (!selectedFactoryId) return

    try {
      await updateFactoryMutation.mutateAsync(factoryFormData)
      toast.success('工場情報を更新しました')
      setIsEditingFactory(false)
    } catch (error) {
      console.error('Failed to update factory:', error)
      toast.error('更新に失敗しました')
    }
  }

  const handleDeleteFactory = async () => {
    if (!selectedFactoryId || !factoryDetail) return

    const confirmed = await confirmDelete(
      `${factoryDetail.company_name} - ${factoryDetail.plant_name}`
    )

    if (confirmed) {
      try {
        await deleteFactoryMutation.mutateAsync(selectedFactoryId)
        toast.success('工場を削除しました')
        setSelectedFactoryId(null)
      } catch (error) {
        console.error('Failed to delete factory:', error)
        toast.error('削除に失敗しました')
      }
    }
  }

  const handleFieldChange = (field: keyof FactoryUpdate, value: string | number) => {
    setFactoryFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleEditLine = (lineId: number) => {
    // Navigate to line edit page or open modal
    router.push(`/factories/lines/${lineId}/edit`)
  }

  const handleDeleteLine = async (lineId: number) => {
    try {
      await factoryApi.deleteLine(lineId)
      toast.success('ラインを削除しました')
      // Refetch factory details to update lines
      window.location.reload() // Simple reload for now
    } catch (error) {
      console.error('Failed to delete line:', error)
      toast.error('ラインの削除に失敗しました')
    }
  }

  const toggleLineExpand = (lineId: number) => {
    const newExpanded = new Set(expandedLines)
    if (newExpanded.has(lineId)) {
      newExpanded.delete(lineId)
    } else {
      newExpanded.add(lineId)
    }
    setExpandedLines(newExpanded)
  }

  // Helper to format break time for display
  const getBreakTimeSummary = (breakTimeDescription?: string, breakMinutes?: number) => {
    if (!breakTimeDescription || breakTimeDescription.trim() === '') {
      return `${breakMinutes || 0}分`
    }
    const lines = formatBreakTimeForDisplay(breakTimeDescription)
    if (lines.length === 0) {
      return `${breakMinutes || 0}分`
    }
    // Take first line (shift) and first period as summary
    const firstLine = lines[0]
    if (firstLine.startsWith('【')) {
      // If we have shift, maybe show shift + first period
      const secondLine = lines[1] || ''
      const summary = secondLine ? `${firstLine} ${secondLine.trim()}` : firstLine
      return `${summary} (${breakMinutes || 0}分)`
    } else {
      // No shift, just show first line
      return `${firstLine} (${breakMinutes || 0}分)`
    }
  }

  // Empty state component
  const EmptyState = ({ message }: { message: string }) => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <p className="text-gray-500 text-lg">{message}</p>
      </div>
    </div>
  )

  return (
    <>
      {/* Breadcrumbs */}
      <Breadcrumbs items={[
        { label: 'ダッシュボード', href: '/' },
        { label: '派遣先企業・工場管理', href: '/factories' }
      ]} />

      {/* Main Content */}
      <div className="flex h-[calc(100vh-120px)] bg-gray-50">
        {/* Left Panel - Factory Tree */}
        <FactoryTree
          factories={factories}
          selectedFactoryId={selectedFactoryId}
          onSelectFactory={handleSelectFactory}
          onCreateNew={handleCreateNew}
          isLoading={isLoadingFactories}
        />

        {/* Right Panel - Factory Details */}
        <div className="flex-1 overflow-y-auto bg-white">
          {selectedFactoryId && factoryDetail ? (
            <div className="p-6">
              {/* Factory Header */}
              <div className="border-b pb-4 mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🏢</span>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">
                        {factoryDetail.company_name} - {factoryDetail.plant_name}
                      </h2>
                      <p className="text-sm text-gray-600 mt-1">
                        工場ID: {factoryDetail.factory_id} |
                        {factoryDetail.lines?.length || 0}ライン |
                        {employees.length}名配属
                      </p>
                    </div>
                  </div>
                  {!isEditingFactory && (
                    <div className="flex gap-2">
                      <button
                        onClick={handleEditFactory}
                        className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        編集
                      </button>
                      <button
                        onClick={handleDeleteFactory}
                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        削除
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Factory Information Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Company Info Card */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📋</span>
                    <h3 className="font-semibold">会社情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">会社名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_name || ''}
                          onChange={(e) => handleFieldChange('company_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_name}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">住所</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_address || ''}
                          onChange={(e) => handleFieldChange('company_address', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_address || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_phone || ''}
                          onChange={(e) => handleFieldChange('company_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Factory Info Card */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📍</span>
                    <h3 className="font-semibold">工場情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">工場名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_name || ''}
                          onChange={(e) => handleFieldChange('plant_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_name}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">住所</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_address || ''}
                          onChange={(e) => handleFieldChange('plant_address', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_address || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_phone || ''}
                          onChange={(e) => handleFieldChange('plant_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Responsible Persons */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">👤</span>
                    <h3 className="font-semibold">派遣先責任者</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">部署</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_department || ''}
                          onChange={(e) => handleFieldChange('client_responsible_department', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_department || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">氏名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_name || ''}
                          onChange={(e) => handleFieldChange('client_responsible_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_name || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_phone || ''}
                          onChange={(e) => handleFieldChange('client_responsible_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Complaint Contact */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📞</span>
                    <h3 className="font-semibold">派遣先苦情担当</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">部署</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_department || ''}
                          onChange={(e) => handleFieldChange('client_complaint_department', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_department || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">氏名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_name || ''}
                          onChange={(e) => handleFieldChange('client_complaint_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_name || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_phone || ''}
                          onChange={(e) => handleFieldChange('client_complaint_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Information Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Contract & Schedule Card */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📅</span>
                    <h3 className="font-semibold">契約・スケジュール情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">契約開始日</label>
                      <p className="font-medium">
                        {factoryDetail.contract_start_date ?
                          new Date(factoryDetail.contract_start_date).toLocaleDateString('ja-JP') : '未設定'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">契約終了日</label>
                      <p className="font-medium">
                        {factoryDetail.contract_end_date ?
                          new Date(factoryDetail.contract_end_date).toLocaleDateString('ja-JP') : '未設定'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">就業時間</label>
                      <p className="font-medium">{factoryDetail.work_hours_description || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">昼勤開始</label>
                      <p className="font-medium">{factoryDetail.day_shift_start || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">昼勤終了</label>
                      <p className="font-medium">{factoryDetail.day_shift_end || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">夜勤開始</label>
                      <p className="font-medium">{factoryDetail.night_shift_start || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">夜勤終了</label>
                      <p className="font-medium">{factoryDetail.night_shift_end || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間外労働上限 (日)</label>
                      <p className="font-medium">{factoryDetail.overtime_max_hours_day ? `${factoryDetail.overtime_max_hours_day}時間` : '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間外労働上限 (月)</label>
                      <p className="font-medium">{factoryDetail.overtime_max_hours_month ? `${factoryDetail.overtime_max_hours_month}時間` : '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">休日労働上限 (月)</label>
                      <p className="font-medium">{factoryDetail.holiday_work_max_days_month ? `${factoryDetail.holiday_work_max_days_month}日` : '-'}</p>
                    </div>
                  </div>
                </div>

                {/* Payment & Agreement Card */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">💰</span>
                    <h3 className="font-semibold">支払・協定情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">締め日</label>
                      <p className="font-medium">{factoryDetail.closing_date || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">支払日</label>
                      <p className="font-medium">{factoryDetail.payment_date || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者締め日</label>
                      <p className="font-medium">{factoryDetail.worker_closing_date || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者支払日</label>
                      <p className="font-medium">{factoryDetail.worker_payment_date || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者カレンダー</label>
                      <p className="font-medium">{factoryDetail.worker_calendar || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">協定期間</label>
                      <p className="font-medium">
                        {factoryDetail.agreement_period ?
                          new Date(factoryDetail.agreement_period).toLocaleDateString('ja-JP') : '未設定'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">説明者</label>
                      <p className="font-medium">{factoryDetail.agreement_explainer || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間単位 (分)</label>
                      <p className="font-medium">{factoryDetail.time_unit_minutes || '15'}分</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">銀行口座</label>
                      <p className="font-medium">{factoryDetail.bank_account || '-'}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Conflict Date & Break Minutes (inline) */}
              <div className="flex flex-wrap gap-6 mb-6">
                <div>
                  <span className="text-sm text-gray-600">📅 抵触日:</span>
                  {isEditingFactory ? (
                    <input
                      type="date"
                      value={factoryFormData.conflict_date || ''}
                      onChange={(e) => handleFieldChange('conflict_date', e.target.value)}
                      className="ml-2 px-3 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    <span className="font-medium ml-2">
                      {factoryDetail.conflict_date ?
                        new Date(factoryDetail.conflict_date).toLocaleDateString('ja-JP') :
                        '未設定'
                      }
                    </span>
                  )}
                </div>
                <div>
                  <span className="text-sm text-gray-600">⏰ 休憩:</span>
                  {isEditingFactory ? (
                    <input
                      type="number"
                      value={factoryFormData.break_minutes || 0}
                      onChange={(e) => handleFieldChange('break_minutes', parseInt(e.target.value))}
                      className="ml-2 px-3 py-1 border border-gray-300 rounded-md w-20"
                      min="0"
                    />
                  ) : (
                    <span className="font-medium ml-2">
                      {getBreakTimeSummary(factoryDetail.break_time_description, factoryDetail.break_minutes)}
                    </span>
                  )}
                </div>
              </div>

              {/* Action Buttons for Factory Edit */}
              {isEditingFactory && (
                <div className="border-t pt-4 mb-6 flex justify-end gap-3">
                  <button
                    onClick={handleCancelEditFactory}
                    className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    disabled={updateFactoryMutation.isPending}
                  >
                    キャンセル
                  </button>
                  <button
                    onClick={handleSaveFactory}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                    disabled={updateFactoryMutation.isPending}
                  >
                    {updateFactoryMutation.isPending ? (
                      <>
                        <span className="animate-spin">⏳</span>
                        保存中...
                      </>
                    ) : (
                      <>
                        💾 保存する
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Production Lines Section */}
              <div className="border-t pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">
                    生産ライン ({factoryDetail.lines?.length || 0})
                  </h3>
                  {!isEditingFactory && (
                    <button
                      onClick={() => router.push(`/factories/${selectedFactoryId}/lines/create`)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      + ライン追加
                    </button>
                  )}
                </div>

                {/* LineCard Components */}
                {isLoadingEmployees ? (
                  <div className="space-y-3">
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {factoryDetail.lines && factoryDetail.lines.length > 0 ? (
                      factoryDetail.lines.map((line: FactoryLineResponse) => {
                        const lineEmployees = employeesByLine.get(line.id) || []
                        return (
                          <LineCard
                            key={line.id}
                            line={line}
                            employees={lineEmployees}
                            baseRate={line.hourly_rate}
                            onEdit={handleEditLine}
                            onDelete={handleDeleteLine}
                            isExpanded={expandedLines.has(line.id)}
                            onToggleExpand={() => toggleLineExpand(line.id)}
                          />
                        )
                      })
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-8 text-center">
                        <span className="text-4xl mb-3 block">🏭</span>
                        <p className="text-gray-600">生産ラインが登録されていません</p>
                        <button
                          onClick={() => router.push(`/factories/${selectedFactoryId}/lines/create`)}
                          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          最初のラインを追加
                        </button>
                      </div>
                    )}

                    {/* Employees without line assignment */}
                    {employeesByLine.has(null) && employeesByLine.get(null)!.length > 0 && (
                      <div className="mt-6 border-t pt-6">
                        <h4 className="text-lg font-medium mb-3 text-gray-700">
                          ライン未割当社員 ({employeesByLine.get(null)!.length}名)
                        </h4>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                            {employeesByLine.get(null)!.map((emp) => (
                              <div key={emp.id} className="bg-white rounded-md px-3 py-2 border border-gray-200">
                                <div className="text-sm font-medium text-gray-900">
                                  {emp.employee_number}
                                </div>
                                <div className="text-xs text-gray-600">
                                  {emp.display_name || emp.full_name_kana || emp.full_name_kanji}
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="mt-3 text-sm text-yellow-700">
                            これらの社員はラインに割り当てられていません。ライン管理から割り当ててください。
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <EmptyState message={isLoadingDetail ? "読み込み中..." : "左側から工場を選択してください"} />
          )}
        </div>
      </div>
    </>
  )
}