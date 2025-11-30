'use client'

import { useState, useEffect, useMemo } from 'react'
import { factoryApi, employeeApi, kobetsuApi } from '@/lib/api'
import type { KobetsuCreate, FactoryListItem, EmployeeListItem } from '@/types'
import {
  HAKEN_MOTO_COMPLAINT_CONTACT,
  HAKEN_MOTO_MANAGER,
  DEFAULT_WORK_CONDITIONS,
} from '@/config/uns-defaults'

interface KobetsuFormProps {
  initialData?: Partial<KobetsuCreate>
  onSubmit: (data: KobetsuCreate) => void
  isLoading?: boolean
}

const WORK_DAYS = ['月', '火', '水', '木', '金', '土', '日']
const RESPONSIBILITY_LEVELS = ['補助的業務', '通常業務', '責任業務']

export function KobetsuForm({ initialData, onSubmit, isLoading }: KobetsuFormProps) {
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
    // 派遣元（UNS企画）の連絡先 - config/uns-defaults.ts で設定
    haken_moto_complaint_contact: { ...HAKEN_MOTO_COMPLAINT_CONTACT },
    haken_saki_complaint_contact: {
      department: '',
      position: '',
      name: '',
      phone: '',
    },
    // 派遣元責任者（UNS企画）- config/uns-defaults.ts で設定
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
  const [employees, setEmployees] = useState<EmployeeListItem[]>([])
  const [loadingEmployees, setLoadingEmployees] = useState(false)
  const [employeeSearch, setEmployeeSearch] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [compatibilityStatus, setCompatibilityStatus] = useState<{
    is_valid: boolean
    compatible_count: number
    incompatible_count: number
    compatible: Array<{
      id: number
      employee_number: string
      full_name_kanji: string
      line_name: string
      status: string
    }>
    incompatible: Array<{
      id: number
      employee_number: string
      full_name_kanji: string
      line_name: string
      issues: Array<{
        type: string
        reason: string
        severity: string
      }>
    }>
    suggestions: string[]
    summary: string
  } | null>(null)
  const [validatingCompatibility, setValidatingCompatibility] = useState(false)

  useEffect(() => {
    async function loadFactories() {
      setLoadingFactories(true)
      try {
        const data = await factoryApi.getList({ limit: 100 })
        setFactories(data)

        // If initialData has factory_id, use it. Otherwise, if there are factories, select none by default
        if (!initialData?.factory_id && data.length > 0) {
            // Keep undefined to force user selection
        }
      } catch (err) {
        // Failed to load factories - error handled silently
      } finally {
        setLoadingFactories(false)
      }
    }
    loadFactories()
  }, [initialData])

  // Load employees
  useEffect(() => {
    async function loadEmployees() {
      setLoadingEmployees(true)
      try {
        const data = await employeeApi.getList({ limit: 1000 })
        setEmployees(data)
      } catch (err) {
        // Failed to load employees - error handled silently
      } finally {
        setLoadingEmployees(false)
      }
    }
    loadEmployees()
  }, [])

  // Validate employee compatibility when selection changes
  useEffect(() => {
    const validateCompatibility = async () => {
      if (!formData.employee_ids || formData.employee_ids.length === 0) {
        setCompatibilityStatus(null)
        return
      }

      if (!formData.factory_id) {
        setCompatibilityStatus(null)
        return
      }

      setValidatingCompatibility(true)
      try {
        const result = await kobetsuApi.validateEmployeeCompatibility({
          employee_ids: formData.employee_ids,
          factory_line_id: formData.factory_id, // TODO: should be factory_line_id, not factory_id
          hourly_rate: formData.hourly_rate || DEFAULT_WORK_CONDITIONS.hourly_rate,
        })
        setCompatibilityStatus(result)
      } catch (err) {
        console.error('Failed to validate compatibility:', err)
        setCompatibilityStatus(null)
      } finally {
        setValidatingCompatibility(false)
      }
    }

    validateCompatibility()
  }, [formData.employee_ids, formData.factory_id, formData.hourly_rate])

  // Filter employees based on search (by 社員№ or name)
  const filteredEmployees = useMemo(() => {
    if (!employeeSearch.trim()) return employees.slice(0, 200) // Show first 200 by default
    const search = employeeSearch.toLowerCase()
    return employees.filter(emp =>
      emp.employee_number?.toLowerCase().includes(search) ||
      emp.full_name_kanji?.toLowerCase().includes(search) ||
      emp.full_name_kana?.toLowerCase().includes(search)
    ).slice(0, 200) // Aumentado a 200 para mejor UX
  }, [employees, employeeSearch])

  // Handle employee selection
  const handleEmployeeToggle = (employeeId: number) => {
    setFormData(prev => {
      const currentIds = prev.employee_ids || []
      const newIds = currentIds.includes(employeeId)
        ? currentIds.filter(id => id !== employeeId)
        : [...currentIds, employeeId]
      return { ...prev, employee_ids: newIds }
    })
  }

  // Get selected employees info
  const selectedEmployees = useMemo(() => {
    return employees.filter(emp => formData.employee_ids?.includes(emp.id))
  }, [employees, formData.employee_ids])

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
            supervisor_position: factory.supervisor_position || '',  // Usa configuración de fábrica, sin defaults
            supervisor_name: factory.supervisor_name || '',
            haken_saki_complaint_contact: {
                department: factory.client_complaint_department || '',
                position: factory.client_complaint_position || '',  // Usa configuración de fábrica
                name: factory.client_complaint_name || '',
                phone: factory.client_complaint_phone || '',
            },
            haken_saki_manager: {
                department: factory.client_responsible_department || '',
                position: factory.client_responsible_position || '',  // Usa configuración de fábrica
                name: factory.client_responsible_name || '',
                phone: factory.client_responsible_phone || '',
            }
        }))
    } catch (err) {
        // Failed to load factory details - error handled silently
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
    }))
  }

  const handleNestedChange = (
    parent: string,
    field: string,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [parent]: {
        ...(prev as any)[parent],
        [field]: value,
      },
    }))
  }

  const handleWorkDaysChange = (day: string) => {
    setFormData((prev) => {
      const currentDays = prev.work_days || []
      const newDays = currentDays.includes(day)
        ? currentDays.filter((d) => d !== day)
        : [...currentDays, day]
      return { ...prev, work_days: newDays }
    })
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.factory_id) {
        newErrors.factory_id = '工場を選択してください'
    }
    if (!formData.employee_ids || formData.employee_ids.length === 0) {
        newErrors.employee_ids = '派遣労働者を最低1名選択してください'
    }
    if (!formData.worksite_name) {
      newErrors.worksite_name = '派遣先名を入力してください'
    }
    if (!formData.worksite_address) {
      newErrors.worksite_address = '所在地を入力してください'
    }
    if (!formData.work_content || formData.work_content.length < 10) {
      newErrors.work_content = '業務内容を10文字以上で入力してください'
    }
    if (!formData.dispatch_start_date) {
      newErrors.dispatch_start_date = '開始日を入力してください'
    }
    if (!formData.dispatch_end_date) {
      newErrors.dispatch_end_date = '終了日を入力してください'
    }
    if (formData.dispatch_start_date && formData.dispatch_end_date) {
      if (formData.dispatch_end_date < formData.dispatch_start_date) {
        newErrors.dispatch_end_date = '終了日は開始日以降にしてください'
      }
      // ✅ 労働者派遣法: 派遣期間は最大3年
      const startDate = new Date(formData.dispatch_start_date)
      const endDate = new Date(formData.dispatch_end_date)
      const monthsDiff = (endDate.getFullYear() - startDate.getFullYear()) * 12 +
                         (endDate.getMonth() - startDate.getMonth())
      if (monthsDiff > 36) {
        newErrors.dispatch_end_date = '派遣期間は36ヶ月(3年)以内である必要があります（労働者派遣法第40条）'
      }
    }
    if (!formData.supervisor_name) {
      newErrors.supervisor_name = '指揮命令者を入力してください'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSubmit(formData as KobetsuCreate)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Section 0: Factory Selection */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣先選択
        </h3>
        <div className="grid grid-cols-1 gap-6">
            <div>
                <label className="form-label">工場を選択 *</label>
                <select
                    name="factory_id"
                    value={formData.factory_id || ''}
                    onChange={handleFactoryChange}
                    className={`form-select ${errors.factory_id ? 'border-red-500' : ''}`}
                    disabled={loadingFactories}
                    required
                >
                    <option value="">-- 選択してください --</option>
                    {factories.map(f => (
                        <option key={f.id} value={f.id}>
                            {f.company_name} - {f.plant_name}
                        </option>
                    ))}
                </select>
                {loadingFactories && <p className="text-sm text-gray-500 mt-1">読み込み中...</p>}
                {errors.factory_id && (
                  <p className="form-error">{errors.factory_id}</p>
                )}
            </div>
        </div>
      </section>

      {/* Section 0.5: Employee Selection */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣労働者選択 *
        </h3>

        {/* Employee Compatibility Status */}
        {compatibilityStatus && (
          <div className="mb-6 border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              {compatibilityStatus.is_valid ? (
                <div className="flex items-center gap-2 text-green-700 bg-green-50 px-3 py-2 rounded">
                  <span className="text-xl">✅</span>
                  <span className="font-semibold">{compatibilityStatus.summary}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-orange-700 bg-orange-50 px-3 py-2 rounded">
                  <span className="text-xl">⚠️</span>
                  <span className="font-semibold">{compatibilityStatus.summary}</span>
                </div>
              )}
            </div>

            {/* Compatible employees */}
            {compatibilityStatus.compatible.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-green-700 mb-2">
                  ✅ Compatible ({compatibilityStatus.compatible_count}):
                </h4>
                <div className="grid grid-cols-1 gap-2">
                  {compatibilityStatus.compatible.map(emp => (
                    <div key={emp.id} className="bg-green-50 border border-green-200 rounded p-2 text-sm">
                      <div className="font-medium text-gray-900">
                        {emp.employee_number} - {emp.full_name_kanji}
                      </div>
                      <div className="text-gray-600 text-xs">
                        Line: {emp.line_name} | Status: {emp.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Incompatible employees */}
            {compatibilityStatus.incompatible.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-red-700 mb-2">
                  ❌ Incompatible - Need Separate Contract ({compatibilityStatus.incompatible_count}):
                </h4>
                <div className="grid grid-cols-1 gap-2">
                  {compatibilityStatus.incompatible.map(emp => (
                    <div key={emp.id} className="bg-red-50 border border-red-200 rounded p-2 text-sm">
                      <div className="font-medium text-gray-900">
                        {emp.employee_number} - {emp.full_name_kanji}
                      </div>
                      <div className="text-gray-600 text-xs mb-1">
                        Line: {emp.line_name}
                      </div>
                      {emp.issues.map((issue, idx) => (
                        <div key={idx} className="text-red-700 text-xs">
                          • {issue.reason}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {compatibilityStatus.suggestions.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <h4 className="text-sm font-semibold text-blue-700 mb-2">💡 Suggestions:</h4>
                <ul className="space-y-1">
                  {compatibilityStatus.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="text-sm text-blue-700">
                      • {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {validatingCompatibility && (
          <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded text-sm text-gray-600">
            Validating employee compatibility...
          </div>
        )}

        {/* Selected employees display */}
        {selectedEmployees.length > 0 && (
          <div className="mb-4">
            <label className="form-label text-sm text-gray-600 mb-2">選択済み ({selectedEmployees.length}名)</label>
            <div className="flex flex-wrap gap-2">
              {selectedEmployees.map(emp => (
                <span
                  key={emp.id}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
                >
                  <span className="font-mono font-medium">{emp.employee_number}</span>
                  <span className="text-primary-600">|</span>
                  <span>{emp.full_name_kanji || emp.full_name_kana}</span>
                  <button
                    type="button"
                    onClick={() => handleEmployeeToggle(emp.id)}
                    className="ml-1 hover:text-red-600"
                    title="削除"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Search input */}
        <div className="mb-3">
          <input
            type="text"
            value={employeeSearch}
            onChange={(e) => setEmployeeSearch(e.target.value)}
            placeholder="社員№ または氏名で検索..."
            className="form-input"
          />
        </div>

        {/* Employee list */}
        <div className={`border rounded-lg max-h-60 overflow-y-auto ${errors.employee_ids ? 'border-red-500' : 'border-gray-200'}`}>
          {loadingEmployees ? (
            <div className="p-4 text-center text-gray-500">読み込み中...</div>
          ) : filteredEmployees.length === 0 ? (
            <div className="p-4 text-center text-gray-500">該当する従業員がありません</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="p-2 text-left w-10"></th>
                  <th className="p-2 text-left font-medium">社員№</th>
                  <th className="p-2 text-left font-medium">氏名</th>
                  <th className="p-2 text-left font-medium">国籍</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map(emp => {
                  const isSelected = formData.employee_ids?.includes(emp.id)
                  return (
                    <tr
                      key={emp.id}
                      onClick={() => handleEmployeeToggle(emp.id)}
                      className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-primary-50' : ''}`}
                    >
                      <td className="p-2">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                      </td>
                      <td className="p-2 font-mono font-medium text-gray-900">{emp.employee_number}</td>
                      <td className="p-2">
                        <div>{emp.full_name_kanji || emp.full_name_kana}</div>
                        {emp.full_name_kanji && emp.full_name_kana && <div className="text-xs text-gray-500">{emp.full_name_kana}</div>}
                      </td>
                      <td className="p-2 text-gray-600">{emp.nationality}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
        {errors.employee_ids && (
          <p className="form-error mt-1">{errors.employee_ids}</p>
        )}
        <p className="text-xs text-gray-500 mt-2">
          {employees.length}名の従業員から選択 • 検索で絞り込み可能
        </p>
      </section>

      {/* Section 1: Basic Info */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          基本情報
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">契約締結日 *</label>
            <input
              type="date"
              name="contract_date"
              value={formData.contract_date}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          <div></div>
          <div>
            <label className="form-label">派遣開始日 *</label>
            <input
              type="date"
              name="dispatch_start_date"
              value={formData.dispatch_start_date}
              onChange={handleChange}
              className={`form-input ${errors.dispatch_start_date ? 'border-red-500' : ''}`}
              required
            />
            {errors.dispatch_start_date && (
              <p className="form-error">{errors.dispatch_start_date}</p>
            )}
          </div>
          <div>
            <label className="form-label">派遣終了日 *</label>
            <input
              type="date"
              name="dispatch_end_date"
              value={formData.dispatch_end_date}
              onChange={handleChange}
              className={`form-input ${errors.dispatch_end_date ? 'border-red-500' : ''}`}
              required
            />
            {errors.dispatch_end_date && (
              <p className="form-error">{errors.dispatch_end_date}</p>
            )}
          </div>
        </div>
      </section>

      {/* Section 2: Work Location */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          就業場所
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">派遣先事業所名 *</label>
            <input
              type="text"
              name="worksite_name"
              value={formData.worksite_name}
              onChange={handleChange}
              className={`form-input ${errors.worksite_name ? 'border-red-500' : ''}`}
              placeholder="例: トヨタ自動車株式会社 田原工場"
              required
            />
            {errors.worksite_name && (
              <p className="form-error">{errors.worksite_name}</p>
            )}
          </div>
          <div>
            <label className="form-label">所在地 *</label>
            <input
              type="text"
              name="worksite_address"
              value={formData.worksite_address}
              onChange={handleChange}
              className={`form-input ${errors.worksite_address ? 'border-red-500' : ''}`}
              placeholder="例: 愛知県田原市緑が浜2号1番地"
              required
            />
            {errors.worksite_address && (
              <p className="form-error">{errors.worksite_address}</p>
            )}
          </div>
          <div>
            <label className="form-label">組織単位</label>
            <input
              type="text"
              name="organizational_unit"
              value={formData.organizational_unit}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 第1製造部"
            />
          </div>
        </div>
      </section>

      {/* Section 3: Work Content */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          業務内容
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">業務内容 *</label>
            <textarea
              name="work_content"
              value={formData.work_content}
              onChange={handleChange}
              className={`form-textarea ${errors.work_content ? 'border-red-500' : ''}`}
              rows={4}
              placeholder="例: 製造ライン作業、検品、梱包業務"
              required
            />
            {errors.work_content && (
              <p className="form-error">{errors.work_content}</p>
            )}
          </div>
          <div>
            <label className="form-label">責任の程度 *</label>
            <select
              name="responsibility_level"
              value={formData.responsibility_level}
              onChange={handleChange}
              className="form-select"
              required
            >
              {RESPONSIBILITY_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Section 4: Supervisor */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          指揮命令者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="form-label">部署 *</label>
            <input
              type="text"
              name="supervisor_department"
              value={formData.supervisor_department}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 製造部"
              required
            />
          </div>
          <div>
            <label className="form-label">役職 *</label>
            <input
              type="text"
              name="supervisor_position"
              value={formData.supervisor_position}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 課長"
              required
            />
          </div>
          <div>
            <label className="form-label">氏名 *</label>
            <input
              type="text"
              name="supervisor_name"
              value={formData.supervisor_name}
              onChange={handleChange}
              className={`form-input ${errors.supervisor_name ? 'border-red-500' : ''}`}
              placeholder="例: 田中太郎"
              required
            />
            {errors.supervisor_name && (
              <p className="form-error">{errors.supervisor_name}</p>
            )}
          </div>
        </div>
      </section>

      {/* Section 5: Working Hours */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          就業時間
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">就業日 *</label>
            <div className="flex flex-wrap gap-2">
              {WORK_DAYS.map((day) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => handleWorkDaysChange(day)}
                  className={`px-4 py-2 rounded-md border ${
                    formData.work_days?.includes(day)
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="form-label">始業時刻 *</label>
              <input
                type="time"
                name="work_start_time"
                value={formData.work_start_time}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            <div>
              <label className="form-label">終業時刻 *</label>
              <input
                type="time"
                name="work_end_time"
                value={formData.work_end_time}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            <div>
              <label className="form-label">休憩時間（分） *</label>
              <input
                type="number"
                name="break_time_minutes"
                value={formData.break_time_minutes}
                onChange={handleChange}
                className="form-input"
                min={0}
                max={180}
                required
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 6: Rates */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣料金
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">基本時間単価（円） *</label>
            <input
              type="number"
              name="hourly_rate"
              value={formData.hourly_rate}
              onChange={handleChange}
              className="form-input"
              min={1000}
              max={10000}
              required
            />
          </div>
          <div>
            <label className="form-label">時間外単価（円） *</label>
            <input
              type="number"
              name="overtime_rate"
              value={formData.overtime_rate}
              onChange={handleChange}
              className="form-input"
              min={1000}
              max={15000}
              required
            />
          </div>
        </div>
      </section>

      {/* Section 7: Complaint Contacts */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          苦情処理担当者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Haken Moto */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣元（UNS企画）</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_moto_complaint_contact?.name}
                onChange={(e) => handleNestedChange('haken_moto_complaint_contact', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_moto_complaint_contact?.phone}
                onChange={(e) => handleNestedChange('haken_moto_complaint_contact', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号 (例: 03-1234-5678)"
              />
            </div>
          </div>

          {/* Haken Saki */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣先</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_saki_complaint_contact?.department}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'department', e.target.value)}
                className="form-input"
                placeholder="部署"
              />
              <input
                type="text"
                value={formData.haken_saki_complaint_contact?.position}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'position', e.target.value)}
                className="form-input"
                placeholder="役職"
              />
              <input
                type="text"
                value={formData.haken_saki_complaint_contact?.name}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_saki_complaint_contact?.phone}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 8: Managers */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          責任者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Haken Moto Manager */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣元責任者</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_moto_manager?.name}
                onChange={(e) => handleNestedChange('haken_moto_manager', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_moto_manager?.phone}
                onChange={(e) => handleNestedChange('haken_moto_manager', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>

          {/* Haken Saki Manager */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣先責任者</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_saki_manager?.department}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'department', e.target.value)}
                className="form-input"
                placeholder="部署"
              />
              <input
                type="text"
                value={formData.haken_saki_manager?.position}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'position', e.target.value)}
                className="form-input"
                placeholder="役職"
              />
              <input
                type="text"
                value={formData.haken_saki_manager?.name}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_saki_manager?.phone}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 9: Notes */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          備考
        </h3>
        <textarea
          name="notes"
          value={formData.notes || ''}
          onChange={handleChange}
          className="form-textarea"
          rows={4}
          placeholder="その他の特記事項"
        />
      </section>

      {/* Submit */}
      <div className="flex justify-end gap-4 pt-6 border-t">
        <button type="button" className="btn-secondary">
          キャンセル
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '契約書を作成'}
        </button>
      </div>
    </form>
  )
}
