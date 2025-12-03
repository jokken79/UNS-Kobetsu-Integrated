'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { factoryApi } from '@/lib/api'
import type { FactoryUpdate, FactoryLineUpdate, FactoryLineCreate } from '@/types'
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'

interface FactoryLine {
  id: number
  line_id: string
  department: string
  line_name: string
  supervisor_department: string
  supervisor_position: string
  supervisor_name: string
  supervisor_phone: string
  job_description: string
  job_description_detail: string
  responsibility_level: string
  hourly_rate: string
  billing_rate: string | null
  overtime_rate: string | null
  night_rate: string | null
  holiday_rate: string | null
  is_active: boolean
  display_order: number
}

// Line Edit Modal Component
function LineEditModal({
  line,
  factoryId,
  onClose,
  onSave,
  isNew = false,
}: {
  line: Partial<FactoryLine> | null
  factoryId: number
  onClose: () => void
  onSave: () => void
  isNew?: boolean
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<Partial<FactoryLine>>({
    line_id: '',
    department: '',
    line_name: '',
    supervisor_department: '',
    supervisor_name: '',
    supervisor_phone: '',
    job_description: '',
    job_description_detail: '',
    responsibility_level: '通常業務',
    hourly_rate: '',
    billing_rate: null,
    overtime_rate: null,
    is_active: true,
    display_order: 0,
    ...line,
  })

  const updateMutation = useMutation({
    mutationFn: (data: FactoryLineUpdate) => factoryApi.updateLine(line!.id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory', factoryId] })
      alert('ライン情報を更新しました')
      onSave()
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: FactoryLineCreate) => factoryApi.createLine(factoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory', factoryId] })
      alert('新規ラインを作成しました')
      onSave()
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const submitData = {
      line_id: formData.line_id || undefined,
      department: formData.department || undefined,
      line_name: formData.line_name || undefined,
      supervisor_department: formData.supervisor_department || undefined,
      supervisor_name: formData.supervisor_name || undefined,
      supervisor_phone: formData.supervisor_phone || undefined,
      job_description: formData.job_description || undefined,
      job_description_detail: formData.job_description_detail || undefined,
      responsibility_level: formData.responsibility_level || undefined,
      hourly_rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : undefined,
      billing_rate: formData.billing_rate ? parseFloat(formData.billing_rate) : undefined,
      overtime_rate: formData.overtime_rate ? parseFloat(formData.overtime_rate) : undefined,
      is_active: formData.is_active,
      display_order: formData.display_order,
    }

    if (isNew) {
      createMutation.mutate(submitData as FactoryLineCreate)
    } else {
      updateMutation.mutate(submitData as FactoryLineUpdate)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        <div className="bg-purple-600 text-white px-6 py-4 flex items-center justify-between flex-shrink-0">
          <h3 className="text-lg font-bold">
            {isNew ? '新規ライン作成' : 'ライン編集'}
          </h3>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ラインID</label>
              <input
                type="text"
                name="line_id"
                value={formData.line_id || ''}
                onChange={handleChange}
                placeholder="例: Factory-10"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">表示順</label>
              <input
                type="number"
                name="display_order"
                value={formData.display_order || 0}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">配属先 (部署)</label>
              <input
                type="text"
                name="department"
                value={formData.department || ''}
                onChange={handleChange}
                placeholder="例: 製造部"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ライン名</label>
              <input
                type="text"
                name="line_name"
                value={formData.line_name || ''}
                onChange={handleChange}
                placeholder="例: 製造1課"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          {/* Supervisor Info */}
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-medium text-purple-800 mb-3">指揮命令者</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">部署</label>
                <input
                  type="text"
                  name="supervisor_department"
                  value={formData.supervisor_department || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">役職・氏名</label>
                <input
                  type="text"
                  name="supervisor_name"
                  value={formData.supervisor_name || ''}
                  onChange={handleChange}
                  placeholder="例: 課長 山田太郎"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-gray-600 mb-1">電話番号</label>
                <input
                  type="tel"
                  name="supervisor_phone"
                  value={formData.supervisor_phone || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">業務内容</label>
            <textarea
              name="job_description"
              value={formData.job_description || ''}
              onChange={handleChange}
              rows={2}
              placeholder="例: 機械オペレーター及び機械メンテナンス他付随する業務"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">業務内容（詳細）</label>
            <textarea
              name="job_description_detail"
              value={formData.job_description_detail || ''}
              onChange={handleChange}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">責任の程度</label>
            <select
              name="responsibility_level"
              value={formData.responsibility_level || '通常業務'}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="通常業務">通常業務</option>
              <option value="リーダー">リーダー</option>
              <option value="管理職">管理職</option>
            </select>
          </div>

          {/* Rate Info */}
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-medium text-green-800 mb-3">料金情報</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">時給単価 (円)</label>
                <input
                  type="number"
                  name="hourly_rate"
                  value={formData.hourly_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">請求単価 (円)</label>
                <input
                  type="number"
                  name="billing_rate"
                  value={formData.billing_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">時間外単価 (円)</label>
                <input
                  type="number"
                  name="overtime_rate"
                  value={formData.overtime_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              checked={formData.is_active ?? true}
              onChange={handleChange}
              className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
              有効
            </label>
          </div>
          </div>{/* End scrollable area */}

          {/* Actions - Fixed at bottom */}
          <div className="flex justify-end gap-3 p-4 border-t bg-gray-50 flex-shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending || createMutation.isPending}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
            >
              {updateMutation.isPending || createMutation.isPending ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function EditFactoryPage() {
  const router = useRouter()
  const params = useParams()
  const queryClient = useQueryClient()
  const factoryId = parseInt(params.id as string)

  const [formData, setFormData] = useState<Partial<FactoryUpdate>>({})
  const [isEditing, setIsEditing] = useState(false)
  const [expandedLines, setExpandedLines] = useState<Set<number>>(new Set())
  const [editingLine, setEditingLine] = useState<FactoryLine | null>(null)
  const [isCreatingLine, setIsCreatingLine] = useState(false)

  // Fetch factory data
  const { data: factory, isLoading } = useQuery({
    queryKey: ['factory', factoryId],
    queryFn: () => factoryApi.getById(factoryId),
  })

  // Update formData when factory data loads
  useEffect(() => {
    if (factory) {
      setFormData({
        company_name: factory.company_name,
        company_address: factory.company_address,
        company_phone: factory.company_phone,
        company_fax: factory.company_fax,
        client_responsible_department: factory.client_responsible_department,
        client_responsible_name: factory.client_responsible_name,
        client_responsible_phone: factory.client_responsible_phone,
        client_complaint_department: factory.client_complaint_department,
        client_complaint_name: factory.client_complaint_name,
        client_complaint_phone: factory.client_complaint_phone,
        plant_name: factory.plant_name,
        plant_address: factory.plant_address,
        plant_phone: factory.plant_phone,
        work_hours_description: factory.work_hours_description,
        break_time_description: factory.break_time_description,
        break_minutes: factory.break_minutes,
        conflict_date: factory.conflict_date,
        is_active: factory.is_active,
        notes: factory.notes,
      })
    }
  }, [factory])

  const updateMutation = useMutation({
    mutationFn: (data: FactoryUpdate) => factoryApi.update(factoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory', factoryId] })
      queryClient.invalidateQueries({ queryKey: ['factories'] })
      alert('工場情報を更新しました')
      setIsEditing(false)
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => factoryApi.delete(factoryId),
    onSuccess: () => {
      alert('工場を削除しました（無効に変更）')
      router.push('/factories')
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const deleteLineMutation = useMutation({
    mutationFn: (lineId: number) => factoryApi.deleteLine(lineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory', factoryId] })
      alert('ラインを削除しました（無効に変更）')
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData as FactoryUpdate)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }))
  }

  const handleDelete = () => {
    if (confirm('本当にこの工場を削除しますか？（無効に変更されます）')) {
      deleteMutation.mutate()
    }
  }

  const handleDeleteLine = (lineId: number, lineName: string) => {
    if (confirm(`本当にライン「${lineName}」を削除しますか？（無効に変更されます）`)) {
      deleteLineMutation.mutate(lineId)
    }
  }

  const toggleLineExpand = (lineId: number) => {
    setExpandedLines(prev => {
      const next = new Set(prev)
      if (next.has(lineId)) {
        next.delete(lineId)
      } else {
        next.add(lineId)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-4">読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!factory) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600">工場が見つかりません</p>
        </div>
      </div>
    )
  }

  const lines: FactoryLine[] = factory.lines || []

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        {/* Breadcrumbs */}
        <Breadcrumbs
          items={[
            dashboardBreadcrumb,
            { label: '派遣先企業', href: '/factories' },
            { label: factory.company_name || '工場詳細' }
          ]}
          className="mb-6"
        />

        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">工場情報</h1>
            <p className="text-gray-600 mt-2">
              {factory.company_name} - {factory.plant_name}
            </p>
          </div>
          <div className="flex gap-3">
            {!isEditing ? (
              <>
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  編集
                </button>
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  戻る
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false)
                  if (factory) {
                    setFormData({
                      company_name: factory.company_name,
                      plant_name: factory.plant_name,
                    })
                  }
                }}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                キャンセル
              </button>
            )}
          </div>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
          {/* Company Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              派遣先企業情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">企業名</label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">住所</label>
                <input
                  type="text"
                  name="company_address"
                  value={formData.company_address || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">電話番号</label>
                <input
                  type="tel"
                  name="company_phone"
                  value={formData.company_phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">FAX</label>
                <input
                  type="tel"
                  name="company_fax"
                  value={formData.company_fax || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Plant Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              工場情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">工場名</label>
                <input
                  type="text"
                  name="plant_name"
                  value={formData.plant_name || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">電話番号</label>
                <input
                  type="tel"
                  name="plant_phone"
                  value={formData.plant_phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">住所</label>
                <input
                  type="text"
                  name="plant_address"
                  value={formData.plant_address || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">抵触日</label>
                <input
                  type="date"
                  name="conflict_date"
                  value={formData.conflict_date || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Responsible Persons */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              派遣先責任者・苦情処理担当者
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 派遣先責任者 */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-3">派遣先責任者</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">部署</label>
                    <input
                      type="text"
                      name="client_responsible_department"
                      value={formData.client_responsible_department || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">氏名</label>
                    <input
                      type="text"
                      name="client_responsible_name"
                      value={formData.client_responsible_name || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">電話</label>
                    <input
                      type="tel"
                      name="client_responsible_phone"
                      value={formData.client_responsible_phone || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                </div>
              </div>

              {/* 苦情処理担当者 */}
              <div className="bg-orange-50 p-4 rounded-lg">
                <h3 className="font-medium text-orange-800 mb-3">苦情処理担当者</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">部署</label>
                    <input
                      type="text"
                      name="client_complaint_department"
                      value={formData.client_complaint_department || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">氏名</label>
                    <input
                      type="text"
                      name="client_complaint_name"
                      value={formData.client_complaint_name || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">電話</label>
                    <input
                      type="tel"
                      name="client_complaint_phone"
                      value={formData.client_complaint_phone || ''}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-white"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Work Schedule */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              就業時間
            </h2>
            <div className="grid grid-cols-1 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">就業時間</label>
                <textarea
                  name="work_hours_description"
                  value={formData.work_hours_description || ''}
                  onChange={handleChange}
                  rows={2}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">休憩時間</label>
                <textarea
                  name="break_time_description"
                  value={formData.break_time_description || ''}
                  onChange={handleChange}
                  rows={2}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">備考</label>
            <textarea
              name="notes"
              value={formData.notes || ''}
              onChange={handleChange}
              rows={3}
              disabled={!isEditing}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
          </div>

          {/* Actions */}
          {isEditing && (
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-gray-400"
              >
                削除
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
              >
                {updateMutation.isPending ? '更新中...' : '保存'}
              </button>
            </div>
          )}
        </form>

        {/* Production Lines Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">配属先・ライン情報</h2>
                  <p className="text-purple-100 text-sm">{lines.length}ライン登録</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsCreatingLine(true)}
                className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors text-sm font-medium"
              >
                + 新規ライン追加
              </button>
            </div>
          </div>

          {lines.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>ラインが登録されていません</p>
              <button
                type="button"
                onClick={() => setIsCreatingLine(true)}
                className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                最初のラインを追加
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {lines.map((line) => (
                <div key={line.id} className="hover:bg-gray-50">
                  {/* Line Header - Clickable */}
                  <div
                    onClick={() => toggleLineExpand(line.id)}
                    className="px-6 py-4 cursor-pointer flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <span className="text-purple-600 font-bold text-sm">
                          {line.line_id?.replace('Factory-', '') || '#'}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{line.department}</span>
                          <span className="text-gray-400">/</span>
                          <span className="text-gray-700">{line.line_name}</span>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          指揮命令者: <span className="font-medium text-gray-700">{line.supervisor_name || '未設定'}</span>
                          {line.hourly_rate && (
                            <span className="ml-4">時給: <span className="font-medium text-green-600">¥{parseFloat(line.hourly_rate).toLocaleString()}</span></span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${line.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {line.is_active ? '有効' : '無効'}
                      </span>
                      <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${expandedLines.has(line.id) ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>

                  {/* Expanded Line Details */}
                  {expandedLines.has(line.id) && (
                    <div className="px-6 pb-6 bg-gray-50 border-t border-gray-100">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                        {/* 指揮命令者 */}
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                            <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            指揮命令者
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-500">部署:</span>
                              <span className="font-medium">{line.supervisor_department || '-'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">役職・氏名:</span>
                              <span className="font-medium">{line.supervisor_name || '-'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">電話:</span>
                              <span className="font-medium">{line.supervisor_phone || '-'}</span>
                            </div>
                          </div>
                        </div>

                        {/* 料金情報 */}
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                            <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            料金情報
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-500">時給:</span>
                              <span className="font-medium text-green-600">¥{line.hourly_rate ? parseFloat(line.hourly_rate).toLocaleString() : '-'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">請求単価:</span>
                              <span className="font-medium">{line.billing_rate ? `¥${parseFloat(line.billing_rate).toLocaleString()}` : '-'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">時間外:</span>
                              <span className="font-medium">{line.overtime_rate ? `¥${parseFloat(line.overtime_rate).toLocaleString()}` : '-'}</span>
                            </div>
                          </div>
                        </div>

                        {/* 業務内容 */}
                        <div className="md:col-span-2 bg-white p-4 rounded-lg border border-gray-200">
                          <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                            業務内容
                          </h4>
                          <p className="text-sm text-gray-700">{line.job_description || '未設定'}</p>
                          {line.job_description_detail && (
                            <p className="text-sm text-gray-500 mt-2">{line.job_description_detail}</p>
                          )}
                          <div className="mt-3 flex items-center gap-2">
                            <span className="text-xs text-gray-500">責任の程度:</span>
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">{line.responsibility_level || '通常業務'}</span>
                          </div>
                        </div>
                      </div>

                      {/* Line Actions */}
                      <div className="mt-4 flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingLine(line)
                          }}
                          className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                        >
                          編集
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteLine(line.id, line.line_name || line.department || 'このライン')
                          }}
                          disabled={deleteLineMutation.isPending}
                          className="px-4 py-2 text-sm border border-red-300 rounded-lg text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                        >
                          削除
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Line Edit Modal */}
      {editingLine && (
        <LineEditModal
          line={editingLine}
          factoryId={factoryId}
          onClose={() => setEditingLine(null)}
          onSave={() => setEditingLine(null)}
        />
      )}

      {/* Line Create Modal */}
      {isCreatingLine && (
        <LineEditModal
          line={null}
          factoryId={factoryId}
          onClose={() => setIsCreatingLine(false)}
          onSave={() => setIsCreatingLine(false)}
          isNew={true}
        />
      )}
    </div>
  )
}
