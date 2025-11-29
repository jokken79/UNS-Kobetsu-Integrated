'use client'

import { useState, useEffect, useMemo } from 'react'
import { factoryApi } from '@/lib/api'
import type { KobetsuCreate, FactoryListItem } from '@/types'
import { Employee } from '@/lib/base-madre-client'
import { EmployeeSelector } from '@/components/base-madre/EmployeeSelector'
import { EmployeeDetailsCard } from '@/components/base-madre/EmployeeDetailsCard'
import { useBaseMadreHealth } from '@/hooks/use-base-madre'
import {
  HAKEN_MOTO_COMPLAINT_CONTACT,
  HAKEN_MOTO_MANAGER,
  DEFAULT_WORK_CONDITIONS,
} from '@/config/uns-defaults'

interface KobetsuFormHybridProps {
  initialData?: Partial<KobetsuCreate>
  onSubmit: (data: KobetsuCreate) => void
  isLoading?: boolean
}

const WORK_DAYS = ['月', '火', '水', '木', '金', '土', '日']
const RESPONSIBILITY_LEVELS = ['補助的業務', '通常業務', '責任業務']

export function KobetsuFormHybrid({ initialData, onSubmit, isLoading }: KobetsuFormHybridProps) {
  // Base Madre connection status
  const { isHealthy: baseMadreConnected, status: baseMadreStatus } = useBaseMadreHealth()

  const [formData, setFormData] = useState<Partial<KobetsuCreate>>({
    factory_id: undefined,
    employee_ids: [],
    contract_date: new Date().toISOString().split('T')[0],
    dispatch_start_date: '',
    dispatch_end_date: '',
    work_content: '',
    responsibility_level: DEFAULT_WORK_CONDITIONS.responsibility_level,
    worksite_name: '',
    worksite_address: '',
    organizational_unit: '',
    supervisor_department: '',
    supervisor_position: '',
    supervisor_name: '',
    work_days: DEFAULT_WORK_CONDITIONS.work_days,
    work_start_time: DEFAULT_WORK_CONDITIONS.work_start_time,
    work_end_time: DEFAULT_WORK_CONDITIONS.work_end_time,
    break_time_minutes: DEFAULT_WORK_CONDITIONS.break_time_minutes,
    hourly_rate: DEFAULT_WORK_CONDITIONS.hourly_rate,
    overtime_rate: DEFAULT_WORK_CONDITIONS.overtime_rate,
    haken_moto_complaint_contact: { ...HAKEN_MOTO_COMPLAINT_CONTACT },
    haken_saki_complaint_contact: {
      department: '',
      position: '',
      name: '',
      phone: '',
    },
    haken_moto_manager: { ...HAKEN_MOTO_MANAGER },
    haken_saki_manager: {
      department: '',
      position: '',
      name: '',
      phone: '',
    },
    ...initialData,
  })

  const [factories, setFactories] = useState<FactoryListItem[]>([])
  const [loadingFactories, setLoadingFactories] = useState(false)

  // Selected employees from Base Madre
  const [selectedEmployees, setSelectedEmployees] = useState<Employee[]>([])
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Load factories
  useEffect(() => {
    async function loadFactories() {
      setLoadingFactories(true)
      try {
        const data = await factoryApi.getList({ limit: 100 })
        setFactories(data)
      } catch (err) {
        // Failed to load factories - error handled silently
      } finally {
        setLoadingFactories(false)
      }
    }
    loadFactories()
  }, [initialData])

  // Handle employee selection from Base Madre
  const handleEmployeeSelect = (employeeId: number, employee: Employee) => {
    // Check if already selected
    if (selectedEmployees.find(e => e.id === employeeId)) {
      return
    }

    // Add to selected list
    setSelectedEmployees(prev => [...prev, employee])

    // Update form data with employee IDs
    setFormData(prev => ({
      ...prev,
      employee_ids: [...(prev.employee_ids || []), employeeId]
    }))

    // Clear temporary selection
    setSelectedEmployeeId(null)
  }

  // Remove employee from selection
  const handleRemoveEmployee = (employeeId: number) => {
    setSelectedEmployees(prev => prev.filter(e => e.id !== employeeId))
    setFormData(prev => ({
      ...prev,
      employee_ids: (prev.employee_ids || []).filter(id => id !== employeeId)
    }))
  }

  const handleFactoryChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const factoryId = Number(e.target.value)
    if (!factoryId) return

    setFormData(prev => ({ ...prev, factory_id: factoryId }))

    // Fetch detailed factory data to pre-fill form
    try {
      const factory = await factoryApi.getById(factoryId)
      setFormData(prev => ({
        ...prev,
        factory_id: factoryId,
        worksite_name: factory.plant_name,
        worksite_address: factory.plant_address || factory.company_address || '',
        supervisor_department: factory.supervisor_department || '',
        supervisor_name: factory.supervisor_name || '',
        haken_saki_complaint_contact: {
          department: factory.client_complaint_department || '',
          position: '',
          name: factory.client_complaint_name || '',
          phone: factory.client_complaint_phone || '',
        },
        haken_saki_manager: {
          department: factory.supervisor_department || '',
          position: factory.supervisor_position || '',
          name: factory.supervisor_name || '',
          phone: factory.supervisor_phone || '',
        },
      }))
    } catch (err) {
      // Failed to load factory details - error handled silently
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    const newErrors: Record<string, string> = {}
    if (!formData.factory_id) newErrors.factory_id = '派遣先を選択してください'
    if (!formData.employee_ids || formData.employee_ids.length === 0) {
      newErrors.employee_ids = '少なくとも1人の労働者を選択してください'
    }
    if (!formData.dispatch_start_date) newErrors.dispatch_start_date = '派遣期間（開始）を入力してください'
    if (!formData.dispatch_end_date) newErrors.dispatch_end_date = '派遣期間（終了）を入力してください'
    if (!formData.work_content) newErrors.work_content = '業務内容を入力してください'

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setErrors({})
    onSubmit(formData as KobetsuCreate)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Base Madre Connection Status */}
      <div className={`rounded-lg p-4 border-2 ${
        baseMadreConnected
          ? 'bg-green-50 border-green-500'
          : 'bg-yellow-50 border-yellow-500'
      }`}>
        <div className="flex items-center gap-3">
          {baseMadreConnected ? (
            <>
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div className="flex-1">
                <p className="font-semibold text-green-900">✅ Base Madre 接続済み</p>
                <p className="text-sm text-green-700">従業員データはリアルタイムで取得されます</p>
              </div>
            </>
          ) : (
            <>
              <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <p className="font-semibold text-yellow-900">⚠️ Base Madre 未接続</p>
                <p className="text-sm text-yellow-700">ローカルデータベースから従業員を選択します</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Section 1: Employees from Base Madre */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">
            1. 労働者の選択 {baseMadreConnected && <span className="text-blue-600 text-sm ml-2">(Base Madre)</span>}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            派遣する労働者を検索して選択してください
          </p>
        </div>
        <div className="card-body space-y-4">
          {/* Employee Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              従業員を検索 *
            </label>
            <EmployeeSelector
              value={selectedEmployeeId}
              onChange={handleEmployeeSelect}
              companyId={formData.factory_id}
              placeholder="名前、メール、または従業員IDで検索..."
            />
            {errors.employee_ids && (
              <p className="text-red-600 text-sm mt-1">{errors.employee_ids}</p>
            )}
          </div>

          {/* Selected Employees List */}
          {selectedEmployees.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">
                選択された労働者 ({selectedEmployees.length}名)
              </h4>
              <div className="space-y-3">
                {selectedEmployees.map((employee) => (
                  <div
                    key={employee.id}
                    className="bg-blue-50 border border-blue-200 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                          {employee.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{employee.name}</p>
                          {employee.name_kana && (
                            <p className="text-sm text-gray-600">{employee.name_kana}</p>
                          )}
                          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                            <span>ID: {employee.employee_id || employee.id}</span>
                            {employee.company_name && (
                              <>
                                <span>•</span>
                                <span>{employee.company_name}</span>
                              </>
                            )}
                            {employee.hourly_rate && (
                              <>
                                <span>•</span>
                                <span>¥{employee.hourly_rate.toLocaleString()}/時</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveEmployee(employee.id)}
                        className="ml-4 text-red-600 hover:text-red-800 p-2"
                        title="削除"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section 2: Factory Selection */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">2. 派遣先の選択</h3>
        </div>
        <div className="card-body">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            派遣先企業 *
          </label>
          <select
            value={formData.factory_id || ''}
            onChange={handleFactoryChange}
            className="input-field"
            disabled={loadingFactories}
          >
            <option value="">-- 選択してください --</option>
            {factories.map(factory => (
              <option key={factory.id} value={factory.id}>
                {factory.company_name} - {factory.plant_name}
              </option>
            ))}
          </select>
          {errors.factory_id && (
            <p className="text-red-600 text-sm mt-1">{errors.factory_id}</p>
          )}
        </div>
      </div>

      {/* Section 3: Contract Period */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">3. 契約期間</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                契約日
              </label>
              <input
                type="date"
                value={formData.contract_date}
                onChange={(e) => setFormData({...formData, contract_date: e.target.value})}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                派遣期間（開始） *
              </label>
              <input
                type="date"
                value={formData.dispatch_start_date}
                onChange={(e) => setFormData({...formData, dispatch_start_date: e.target.value})}
                className="input-field"
              />
              {errors.dispatch_start_date && (
                <p className="text-red-600 text-sm mt-1">{errors.dispatch_start_date}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                派遣期間（終了） *
              </label>
              <input
                type="date"
                value={formData.dispatch_end_date}
                onChange={(e) => setFormData({...formData, dispatch_end_date: e.target.value})}
                className="input-field"
              />
              {errors.dispatch_end_date && (
                <p className="text-red-600 text-sm mt-1">{errors.dispatch_end_date}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Section 4: Work Details */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">4. 業務内容</h3>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              業務内容 *
            </label>
            <textarea
              value={formData.work_content}
              onChange={(e) => setFormData({...formData, work_content: e.target.value})}
              rows={4}
              className="input-field"
              placeholder="例：自動車部品の組立作業、検査業務"
            />
            {errors.work_content && (
              <p className="text-red-600 text-sm mt-1">{errors.work_content}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              責任の程度
            </label>
            <select
              value={formData.responsibility_level}
              onChange={(e) => setFormData({...formData, responsibility_level: e.target.value})}
              className="input-field"
            >
              {RESPONSIBILITY_LEVELS.map(level => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={() => window.history.back()}
          className="btn-secondary"
        >
          キャンセル
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary"
        >
          {isLoading ? '作成中...' : '契約書を作成'}
        </button>
      </div>
    </form>
  )
}
