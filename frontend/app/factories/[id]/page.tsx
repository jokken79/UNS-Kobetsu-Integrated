'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { factoryApi } from '@/lib/api'
import type { FactoryUpdate, FactoryLineUpdate, FactoryLineCreate } from '@/types'
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'
import { formatBreakTimeForDisplay } from '@/lib/formatBreakTime'

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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col animate-scale-in">
        <div className="bg-theme-600 text-white px-6 py-4 flex items-center justify-between flex-shrink-0 rounded-t-lg border-b border-theme-700">
          <div>
            <h3 className="text-xl font-bold tracking-tight">
              {isNew ? '✨ 新規ライン作成' : '📝 ライン編集'}
            </h3>
            <p className="text-violet-100 text-sm mt-1">配属先・ライン情報を入力してください</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 w-8 h-8 rounded-lg transition-all duration-200 flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="p-6 space-y-5 overflow-y-auto flex-1 scrollbar-thin">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">ラインID</label>
              <input
                type="text"
                name="line_id"
                value={formData.line_id || ''}
                onChange={handleChange}
                placeholder="例: Factory-10"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">表示順</label>
              <input
                type="number"
                name="display_order"
                value={formData.display_order || 0}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">配属先 (部署)</label>
              <input
                type="text"
                name="department"
                value={formData.department || ''}
                onChange={handleChange}
                placeholder="例: 製造部"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">ライン名</label>
              <input
                type="text"
                name="line_name"
                value={formData.line_name || ''}
                onChange={handleChange}
                placeholder="例: 製造1課"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          {/* Supervisor Info */}
          <div className="bg-purple-50 p-5 rounded-lg border border-purple-200">
            <h4 className="font-bold text-violet-900 mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-violet-500 flex items-center justify-center text-white text-sm">👤</span>
              指揮命令者
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 font-medium mb-1.5">部署</label>
                <input
                  type="text"
                  name="supervisor_department"
                  value={formData.supervisor_department || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 border border-violet-200 rounded-xl focus:ring-2 focus:ring-violet-500 bg-white transition-all"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 font-medium mb-1.5">役職・氏名</label>
                <input
                  type="text"
                  name="supervisor_name"
                  value={formData.supervisor_name || ''}
                  onChange={handleChange}
                  placeholder="例: 課長 山田太郎"
                  className="w-full px-4 py-2.5 border border-violet-200 rounded-xl focus:ring-2 focus:ring-violet-500 bg-white transition-all"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-gray-700 font-medium mb-1.5">電話番号</label>
                <input
                  type="tel"
                  name="supervisor_phone"
                  value={formData.supervisor_phone || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 border border-violet-200 rounded-xl focus:ring-2 focus:ring-violet-500 bg-white transition-all"
                />
              </div>
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">業務内容</label>
            <textarea
              name="job_description"
              value={formData.job_description || ''}
              onChange={handleChange}
              rows={2}
              placeholder="例: 機械オペレーター及び機械メンテナンス他付随する業務"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">業務内容（詳細）</label>
            <textarea
              name="job_description_detail"
              value={formData.job_description_detail || ''}
              onChange={handleChange}
              rows={2}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">責任の程度</label>
            <select
              name="responsibility_level"
              value={formData.responsibility_level || '通常業務'}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
            >
              <option value="通常業務">通常業務</option>
              <option value="リーダー">リーダー</option>
              <option value="管理職">管理職</option>
            </select>
          </div>

          {/* Rate Info */}
          <div className="bg-emerald-50 p-5 rounded-lg border border-emerald-200">
            <h4 className="font-bold text-emerald-900 mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-500 flex items-center justify-center text-white text-sm">💰</span>
              料金情報
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-700 font-medium mb-1.5">時給単価 (円)</label>
                <input
                  type="number"
                  name="hourly_rate"
                  value={formData.hourly_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-4 py-2.5 border border-emerald-200 rounded-xl focus:ring-2 focus:ring-emerald-500 bg-white transition-all"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 font-medium mb-1.5">請求単価 (円)</label>
                <input
                  type="number"
                  name="billing_rate"
                  value={formData.billing_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-4 py-2.5 border border-emerald-200 rounded-xl focus:ring-2 focus:ring-emerald-500 bg-white transition-all"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 font-medium mb-1.5">時間外単価 (円)</label>
                <input
                  type="number"
                  name="overtime_rate"
                  value={formData.overtime_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-4 py-2.5 border border-emerald-200 rounded-xl focus:ring-2 focus:ring-emerald-500 bg-white transition-all"
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              checked={formData.is_active ?? true}
              onChange={handleChange}
              className="w-5 h-5 text-violet-600 rounded-lg focus:ring-violet-500 transition-colors"
            />
            <label htmlFor="is_active" className="text-sm font-semibold text-gray-700 cursor-pointer">
              有効なラインとして登録
            </label>
          </div>
          </div>{/* End scrollable area */}

          {/* Actions - Fixed at bottom */}
          <div className="flex justify-end gap-3 p-5 border-t bg-gray-50 flex-shrink-0 rounded-b-lg">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-white hover:shadow-md transition-all duration-200"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending || createMutation.isPending}
              className="px-6 py-2.5 bg-theme-600 text-white rounded-lg font-semibold hover:bg-theme-700 disabled:bg-gray-400 transition-colors"
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
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-violet-600 border-t-transparent"></div>
          <p className="text-gray-600 mt-4 font-medium">読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!factory) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600 font-medium">工場が見つかりません</p>
        </div>
      </div>
    )
  }

  const lines: FactoryLine[] = factory.lines || []

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
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
      <div className="mb-8 flex items-start justify-between bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div className="flex-1 min-w-0 mr-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-theme-600 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">工場情報</h1>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <p className="text-base text-gray-700 font-medium truncate">
              {factory.company_name}
            </p>
            <span className="text-gray-400 flex-shrink-0">•</span>
            <p className="text-base text-gray-700 font-medium truncate">
              {factory.plant_name}
            </p>
          </div>
          {factory.plant_address && (
            <p className="text-sm text-gray-500 flex items-center gap-2 truncate">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="truncate">{factory.plant_address}</span>
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {!isEditing ? (
            <>
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-theme-600 text-white rounded-lg hover:bg-theme-700 transition-colors font-medium flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                編集
              </button>
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
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
              className="px-6 py-3 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-200 font-semibold"
            >
              キャンセル
            </button>
          )}
        </div>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-8">
        {/* Company Info */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 pb-3 border-b-2 border-blue-500 flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-theme-100 flex items-center justify-center text-blue-600">
              🏢
            </span>
            派遣先企業情報
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">企業名</label>
              <input
                type="text"
                name="company_name"
                value={formData.company_name || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600 transition-all font-medium"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">住所</label>
              <input
                type="text"
                name="company_address"
                value={formData.company_address || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">電話番号</label>
              <input
                type="tel"
                name="company_phone"
                value={formData.company_phone || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">FAX</label>
              <input
                type="tel"
                name="company_fax"
                value={formData.company_fax || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Plant Info */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 pb-3 border-b-2 border-emerald-500 flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
              🏭
            </span>
            工場情報
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">工場名</label>
              <input
                type="text"
                name="plant_name"
                value={formData.plant_name || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600 transition-all font-medium"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">電話番号</label>
              <input
                type="tel"
                name="plant_phone"
                value={formData.plant_phone || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">住所</label>
              <input
                type="text"
                name="plant_address"
                value={formData.plant_address || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">抵触日</label>
              <input
                type="date"
                name="conflict_date"
                value={formData.conflict_date || ''}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-50 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Responsible Persons */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 pb-3 border-b-2 border-violet-500 flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center text-violet-600">
              👥
            </span>
            派遣先責任者・苦情処理担当者
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 派遣先責任者 */}
            <div className="bg-blue-50 p-5 rounded-lg border border-blue-200">
              <h3 className="font-bold text-gray-900 mb-4">派遣先責任者</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">部署</label>
                  <input
                    type="text"
                    name="client_responsible_department"
                    value={formData.client_responsible_department || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">氏名</label>
                  <input
                    type="text"
                    name="client_responsible_name"
                    value={formData.client_responsible_name || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">電話</label>
                  <input
                    type="tel"
                    name="client_responsible_phone"
                    value={formData.client_responsible_phone || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
              </div>
            </div>

            {/* 苦情処理担当者 */}
            <div className="bg-amber-50 p-5 rounded-lg border border-amber-200">
              <h3 className="font-bold text-gray-900 mb-4">苦情処理担当者</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">部署</label>
                  <input
                    type="text"
                    name="client_complaint_department"
                    value={formData.client_complaint_department || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-orange-200 rounded-xl focus:ring-2 focus:ring-orange-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">氏名</label>
                  <input
                    type="text"
                    name="client_complaint_name"
                    value={formData.client_complaint_name || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-orange-200 rounded-xl focus:ring-2 focus:ring-orange-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">電話</label>
                  <input
                    type="tel"
                    name="client_complaint_phone"
                    value={formData.client_complaint_phone || ''}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full px-4 py-2.5 border border-orange-200 rounded-xl focus:ring-2 focus:ring-orange-500 disabled:bg-white/50 bg-white transition-all"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Work Schedule */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 pb-3 border-b-2 border-amber-500 flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
              ⏰
            </span>
            就業時間
          </h2>
          <div className="grid grid-cols-1 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">就業時間</label>
              <textarea
                name="work_hours_description"
                value={formData.work_hours_description || ''}
                onChange={handleChange}
                rows={2}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 disabled:bg-gray-50 transition-all resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                休憩時間
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  ※ 各休憩を番号付きで記入
                </span>
              </label>
              {isEditing ? (
                <div className="space-y-2">
                  <textarea
                    name="break_time_description"
                    value={formData.break_time_description || ''}
                    onChange={handleChange}
                    rows={3}
                    placeholder="例: ①11:00～12:00（１H）　②20:00～21:00（１H）　③21:00～22:00（１H）
または: 昼勤 10:30~10:40・12:40~13:20　夜勤 22:30~22:40"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 transition-all resize-none font-mono text-sm"
                  />
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-xs text-blue-900 font-semibold mb-1.5">📝 入力形式:</p>
                    <ul className="text-xs text-blue-800 space-y-1 ml-4 list-disc">
                      <li><strong>番号付き:</strong> ①11:00～12:00（１H）　②20:00～21:00（１H）　③21:00～22:00（１H）</li>
                      <li><strong>シフト別:</strong> 昼勤 10:30~10:40・12:40~13:20　夜勤 22:30~22:40</li>
                      <li>時間は「～」または「~」で範囲を指定</li>
                      <li>複数の休憩は「　」（全角スペース）で区切る</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 min-h-[80px]">
                  {factory?.break_time_description ? (
                    <div className="space-y-1">
                      {formatBreakTimeForDisplay(factory.break_time_description).map((line, idx) => (
                        <div
                          key={idx}
                          className={line.startsWith('【') ? 'text-gray-900 font-semibold mt-2 first:mt-0' : 'text-gray-700 text-sm'}
                        >
                          {line}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-gray-400">未設定</span>
                  )}
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">カレンダー・休日</label>
              <textarea
                name="calendar_description"
                value={formData.calendar_description || ''}
                onChange={handleChange}
                rows={3}
                disabled={!isEditing}
                placeholder="例: 月～金 (シフトに準ずる) 休日は、土曜日・日曜日・GW(5月2日～5月6日)・夏季休暇（8月13日～8月17日)・年末年始（12月29日～1月5日)"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 disabled:bg-gray-50 transition-all resize-none"
              />
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="mb-8">
          <label className="block text-sm font-semibold text-gray-700 mb-2">備考</label>
          <textarea
            name="notes"
            value={formData.notes || ''}
            onChange={handleChange}
            rows={3}
            disabled={!isEditing}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 transition-all resize-none"
          />
        </div>

        {/* Actions */}
        {isEditing && (
          <div className="flex items-center justify-between pt-6 border-t-2 border-gray-200">
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all duration-200 font-semibold shadow-lg disabled:bg-gray-400 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              削除
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="px-6 py-2.5 bg-theme-600 text-white rounded-lg hover:bg-theme-700 transition-colors font-semibold disabled:bg-gray-400 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              {updateMutation.isPending ? '更新中...' : '保存'}
            </button>
          </div>
        )}
      </form>

      {/* Production Lines Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-white border-b border-gray-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-theme-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">配属先・ライン情報</h2>
                <p className="text-gray-500 text-sm mt-1">
                  <span className="inline-flex items-center px-2 py-0.5 bg-theme-100 rounded-full text-xs font-semibold text-theme-700">
                    {lines.length}ライン登録
                  </span>
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsCreatingLine(true)}
              className="px-4 py-2 bg-theme-600 text-white hover:bg-theme-700 rounded-lg transition-colors font-medium flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              新規ライン追加
            </button>
          </div>
        </div>

        {lines.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">ラインが登録されていません</h3>
            <p className="text-gray-500 mb-6">最初のラインを追加して配属先情報を管理しましょう</p>
            <button
              type="button"
              onClick={() => setIsCreatingLine(true)}
              className="px-5 py-2.5 bg-theme-600 text-white rounded-lg hover:bg-theme-700 font-semibold transition-colors"
            >
              最初のラインを追加
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {lines.map((line, index) => (
              <div key={line.id} className="hover:bg-gray-50/50 transition-all duration-200" style={{ animationDelay: `${index * 50}ms` }}>
                {/* Line Header - Clickable */}
                <div
                  onClick={() => toggleLineExpand(line.id)}
                  className="px-8 py-5 cursor-pointer flex items-center justify-between group"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-12 h-12 bg-theme-100 rounded-lg flex items-center justify-center group-hover:bg-theme-200 transition-colors">
                      <span className="text-violet-600 font-bold text-base">
                        {line.line_id?.replace('Factory-', '') || '#'}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1.5">
                        <span className="font-bold text-gray-900 text-base truncate">{line.department}</span>
                        <span className="text-gray-300 flex-shrink-0">/</span>
                        <span className="text-gray-700 font-medium truncate">{line.line_name}</span>
                      </div>
                      <div className="text-sm text-gray-600 flex flex-wrap items-center gap-x-4 gap-y-1">
                        <span className="flex items-center gap-1.5">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          <span className="font-medium text-gray-700">{line.supervisor_name || '未設定'}</span>
                        </span>
                        {line.hourly_rate && (
                          <span className="flex items-center gap-1.5">
                            <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="font-semibold text-green-600">¥{parseFloat(line.hourly_rate).toLocaleString()}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1.5 text-xs font-bold rounded-full ${line.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {line.is_active ? '有効' : '無効'}
                    </span>
                    <svg
                      className={`w-6 h-6 text-gray-400 transition-transform duration-300 ${expandedLines.has(line.id) ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* Expanded Line Details */}
                {expandedLines.has(line.id) && (
                  <div className="px-8 pb-6 bg-gray-50 border-t border-gray-200 animate-slide-down">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-5">
                      {/* 指揮命令者 */}
                      <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                        <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <svg className="w-5 h-5 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          指揮命令者
                        </h4>
                        <div className="space-y-3 text-sm">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">部署:</span>
                            <span className="font-semibold text-gray-900">{line.supervisor_department || '-'}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">役職・氏名:</span>
                            <span className="font-semibold text-gray-900">{line.supervisor_name || '-'}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">電話:</span>
                            <span className="font-semibold text-gray-900">{line.supervisor_phone || '-'}</span>
                          </div>
                        </div>
                      </div>

                      {/* 料金情報 */}
                      <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                        <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          料金情報
                        </h4>
                        <div className="space-y-3 text-sm">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">時給:</span>
                            <span className="font-bold text-green-600 text-base">¥{line.hourly_rate ? parseFloat(line.hourly_rate).toLocaleString() : '-'}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">請求単価:</span>
                            <span className="font-semibold text-gray-900">{line.billing_rate ? `¥${parseFloat(line.billing_rate).toLocaleString()}` : '-'}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500">時間外:</span>
                            <span className="font-semibold text-gray-900">{line.overtime_rate ? `¥${parseFloat(line.overtime_rate).toLocaleString()}` : '-'}</span>
                          </div>
                        </div>
                      </div>

                      {/* 業務内容 */}
                      <div className="md:col-span-2 bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                        <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          業務内容
                        </h4>
                        <p className="text-sm text-gray-700 leading-relaxed">{line.job_description || '未設定'}</p>
                        {line.job_description_detail && (
                          <p className="text-sm text-gray-500 mt-3 leading-relaxed bg-gray-50 p-3 rounded-lg">{line.job_description_detail}</p>
                        )}
                        <div className="mt-4 flex items-center gap-2">
                          <span className="text-xs text-gray-500 font-medium">責任の程度:</span>
                          <span className="px-3 py-1 bg-theme-100 text-theme-700 text-xs font-bold rounded-full">{line.responsibility_level || '通常業務'}</span>
                        </div>
                      </div>
                    </div>

                    {/* Line Actions */}
                    <div className="mt-5 flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          setEditingLine(line)
                        }}
                        className="px-5 py-2.5 text-sm border-2 border-gray-300 rounded-xl text-gray-700 font-semibold hover:bg-white hover:border-gray-400 hover:shadow-md transition-all duration-200 flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        編集
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteLine(line.id, line.line_name || line.department || 'このライン')
                        }}
                        disabled={deleteLineMutation.isPending}
                        className="px-5 py-2.5 text-sm border-2 border-red-300 rounded-xl text-red-600 font-semibold hover:bg-red-50 hover:border-red-400 transition-all duration-200 disabled:opacity-50 flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
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
