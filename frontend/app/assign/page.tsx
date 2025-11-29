'use client'

/**
 * Employee Assignment Page - 従業員配属ページ
 *
 * Smart workflow for assigning employees to contracts:
 * 1. Select employee
 * 2. Select factory/line
 * 3. Get AI recommendation (add to existing vs create new)
 * 4. Execute assignment
 */

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import FactoryCascadeSelector from '@/components/factory/FactoryCascadeSelector'
import { kobetsuApi, employeeApi } from '@/lib/api'
import type { EmployeeForContract, FactoryCascadeData } from '@/types'

interface AssignmentSuggestion {
  recommendation: 'add_to_existing' | 'create_new'
  reason: string
  employee_id: number
  employee_name: string
  employee_rate: number | null
  existing_contract: {
    id: number
    contract_number: string
    worksite_name: string
    dispatch_start_date: string
    dispatch_end_date: string
    current_workers: number
    hourly_rate: number
  } | null
  rate_difference_pct: number | null
  conflict_date_info: {
    conflict_date: string | null
    days_remaining: number | null
    warning_level: string
    message: string
  }
}

interface AssignmentResult {
  action: string
  contract_id: number
  contract_number?: string
  employee_id: number
  message: string
  warnings?: string[]
}

export default function AssignEmployeePage() {
  const router = useRouter()

  // Step tracking
  const [currentStep, setCurrentStep] = useState(1)

  // Form state
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeForContract | null>(null)
  const [selectedFactory, setSelectedFactory] = useState<FactoryCascadeData | null>(null)
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0])
  const [customRate, setCustomRate] = useState<string>('')
  const [durationMonths, setDurationMonths] = useState(3)

  // Suggestion state
  const [suggestion, setSuggestion] = useState<AssignmentSuggestion | null>(null)
  const [loadingSuggestion, setLoadingSuggestion] = useState(false)

  // Result state
  const [result, setResult] = useState<AssignmentResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Employee search
  const [employeeSearch, setEmployeeSearch] = useState('')
  const [employees, setEmployees] = useState<EmployeeForContract[]>([])
  const [loadingEmployees, setLoadingEmployees] = useState(false)

  // Search employees
  const searchEmployees = useCallback(async () => {
    if (!employeeSearch.trim()) return

    setLoadingEmployees(true)
    try {
      const results = await employeeApi.getForContract({
        search: employeeSearch,
        limit: 20,
      })
      setEmployees(results)
    } catch (err) {
      // Failed to search employees - error handled silently
    } finally {
      setLoadingEmployees(false)
    }
  }, [employeeSearch])

  // Handle factory selection
  const handleFactorySelect = useCallback((data: FactoryCascadeData) => {
    setSelectedFactory(data)
  }, [])

  // Get suggestion
  const getSuggestion = useCallback(async () => {
    if (!selectedEmployee || !selectedFactory) return

    setLoadingSuggestion(true)
    setError(null)

    try {
      const response = await fetch(
        `/api/v1/kobetsu/suggest/assignment?` +
        `employee_id=${selectedEmployee.id}&` +
        `factory_id=${selectedFactory.factory.id}&` +
        `factory_line_id=${selectedFactory.line.id}&` +
        `start_date=${startDate}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      )

      if (!response.ok) throw new Error('Failed to get suggestion')

      const data = await response.json()
      setSuggestion(data)
      setCurrentStep(3)
    } catch (err) {
      setError('推奨を取得できませんでした')
      // Error getting suggestion - already set in state
    } finally {
      setLoadingSuggestion(false)
    }
  }, [selectedEmployee, selectedFactory, startDate])

  // Execute assignment
  const executeAssignment = useCallback(async (action: 'add_to_existing' | 'create_new') => {
    if (!selectedEmployee || !selectedFactory) return

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        employee_id: selectedEmployee.id.toString(),
        factory_id: selectedFactory.factory.id.toString(),
        factory_line_id: selectedFactory.line.id.toString(),
        start_date: startDate,
        action: action,
        duration_months: durationMonths.toString(),
      })

      if (action === 'add_to_existing' && suggestion?.existing_contract) {
        params.append('existing_contract_id', suggestion.existing_contract.id.toString())
      }

      if (customRate) {
        params.append('hourly_rate', customRate)
      }

      const response = await fetch(`/api/v1/kobetsu/assign-employee?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Assignment failed')
      }

      const data = await response.json()
      setResult(data)
      setCurrentStep(4)
    } catch (err: any) {
      setError(err.message || '配属に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [selectedEmployee, selectedFactory, startDate, customRate, durationMonths, suggestion])

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">従業員配属 - Employee Assignment</h1>

      {/* Progress Steps */}
      <div className="flex items-center mb-8">
        {[1, 2, 3, 4].map((step) => (
          <div key={step} className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                currentStep >= step
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {step}
            </div>
            {step < 4 && (
              <div
                className={`w-16 h-1 ${
                  currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step Labels */}
      <div className="flex justify-between mb-8 text-sm">
        <span className={currentStep >= 1 ? 'text-blue-600' : 'text-gray-400'}>
          従業員選択
        </span>
        <span className={currentStep >= 2 ? 'text-blue-600' : 'text-gray-400'}>
          派遣先選択
        </span>
        <span className={currentStep >= 3 ? 'text-blue-600' : 'text-gray-400'}>
          推奨確認
        </span>
        <span className={currentStep >= 4 ? 'text-blue-600' : 'text-gray-400'}>
          完了
        </span>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Select Employee */}
      {currentStep === 1 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Step 1: 従業員を選択</h2>

          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={employeeSearch}
              onChange={(e) => setEmployeeSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchEmployees()}
              placeholder="社員番号または氏名で検索..."
              className="flex-1 px-4 py-2 border rounded-md"
            />
            <button
              onClick={searchEmployees}
              disabled={loadingEmployees}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loadingEmployees ? '検索中...' : '検索'}
            </button>
          </div>

          {employees.length > 0 && (
            <div className="border rounded-md divide-y max-h-64 overflow-y-auto">
              {employees.map((emp) => (
                <div
                  key={emp.id}
                  onClick={() => {
                    setSelectedEmployee(emp)
                    setCurrentStep(2)
                  }}
                  className={`p-3 cursor-pointer hover:bg-blue-50 ${
                    selectedEmployee?.id === emp.id ? 'bg-blue-100' : ''
                  }`}
                >
                  <div className="flex justify-between">
                    <div>
                      <span className="font-medium">{emp.full_name_kanji}</span>
                      <span className="text-gray-500 ml-2">({emp.full_name_kana})</span>
                    </div>
                    <span className="text-gray-600">{emp.employee_number}</span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {emp.nationality} | {emp.is_indefinite_employment ? '無期雇用' : '有期雇用'}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedEmployee && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800">
                選択中: <strong>{selectedEmployee.full_name_kanji}</strong> ({selectedEmployee.employee_number})
              </p>
              <button
                onClick={() => setCurrentStep(2)}
                className="mt-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                次へ
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Select Factory */}
      {currentStep === 2 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Step 2: 派遣先を選択</h2>

          <div className="mb-4 p-3 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-600">
              選択中の従業員: <strong>{selectedEmployee?.full_name_kanji}</strong>
            </p>
          </div>

          <FactoryCascadeSelector
            onSelect={handleFactorySelect}
            className="mb-6"
          />

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                開始日 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                個別単価 (オプション)
              </label>
              <input
                type="number"
                value={customRate}
                onChange={(e) => setCustomRate(e.target.value)}
                placeholder="空欄で従業員の単価を使用"
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
          </div>

          {selectedFactory && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-blue-800">
                選択中: <strong>{selectedFactory.factory.company_name}</strong> →
                <strong> {selectedFactory.factory.plant_name}</strong> →
                <strong> {selectedFactory.line.line_name || 'デフォルト'}</strong>
              </p>
              {selectedFactory.factory.conflict_date && (
                <p className="text-sm text-orange-600 mt-1">
                  抵触日: {selectedFactory.factory.conflict_date}
                </p>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              戻る
            </button>
            <button
              onClick={getSuggestion}
              disabled={!selectedFactory || loadingSuggestion}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loadingSuggestion ? '分析中...' : '推奨を取得'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Review Suggestion */}
      {currentStep === 3 && suggestion && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Step 3: 推奨を確認</h2>

          {/* Conflict Date Warning */}
          {suggestion.conflict_date_info.warning_level !== 'ok' && (
            <div className={`mb-4 p-4 rounded-md border ${
              suggestion.conflict_date_info.warning_level === 'danger' ||
              suggestion.conflict_date_info.warning_level === 'expired'
                ? 'bg-red-50 border-red-200 text-red-800'
                : 'bg-yellow-50 border-yellow-200 text-yellow-800'
            }`}>
              <p className="font-medium">抵触日警告</p>
              <p>{suggestion.conflict_date_info.message}</p>
            </div>
          )}

          {/* Recommendation */}
          <div className={`p-4 rounded-md border mb-6 ${
            suggestion.recommendation === 'add_to_existing'
              ? 'bg-green-50 border-green-200'
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-2xl ${
                suggestion.recommendation === 'add_to_existing' ? 'text-green-600' : 'text-blue-600'
              }`}>
                {suggestion.recommendation === 'add_to_existing' ? '✓' : '+'}
              </span>
              <span className="text-lg font-semibold">
                {suggestion.recommendation === 'add_to_existing'
                  ? '既存契約に追加'
                  : '新規契約を作成'}
              </span>
            </div>
            <p className="text-gray-700">{suggestion.reason}</p>
          </div>

          {/* Employee Info */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-500">従業員</p>
              <p className="font-medium">{suggestion.employee_name}</p>
              <p className="text-sm">
                単価: {suggestion.employee_rate ? `¥${suggestion.employee_rate}` : '未設定'}
              </p>
            </div>

            {suggestion.existing_contract && (
              <div className="p-3 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-500">既存契約</p>
                <p className="font-medium">{suggestion.existing_contract.contract_number}</p>
                <p className="text-sm">
                  {suggestion.existing_contract.current_workers}名 |
                  ¥{suggestion.existing_contract.hourly_rate}
                </p>
                <p className="text-sm text-gray-500">
                  〜{suggestion.existing_contract.dispatch_end_date}
                </p>
                {suggestion.rate_difference_pct !== null && suggestion.rate_difference_pct > 0 && (
                  <p className="text-sm text-orange-600 mt-1">
                    単価差: {suggestion.rate_difference_pct}%
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Duration Selection (for new contract) */}
          {suggestion.recommendation === 'create_new' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                契約期間
              </label>
              <select
                value={durationMonths}
                onChange={(e) => setDurationMonths(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value={1}>1ヶ月</option>
                <option value={2}>2ヶ月</option>
                <option value={3}>3ヶ月</option>
                <option value={6}>6ヶ月</option>
                <option value={12}>12ヶ月</option>
              </select>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              戻る
            </button>

            {suggestion.recommendation === 'add_to_existing' && suggestion.existing_contract ? (
              <>
                <button
                  onClick={() => executeAssignment('add_to_existing')}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? '処理中...' : '既存契約に追加'}
                </button>
                <button
                  onClick={() => executeAssignment('create_new')}
                  disabled={loading}
                  className="px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 disabled:opacity-50"
                >
                  新規契約を作成
                </button>
              </>
            ) : (
              <button
                onClick={() => executeAssignment('create_new')}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '処理中...' : '新規契約を作成'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Step 4: Result */}
      {currentStep === 4 && result && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Step 4: 完了</h2>

          <div className="p-4 bg-green-50 border border-green-200 rounded-md mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl text-green-600">✓</span>
              <span className="text-lg font-semibold text-green-800">配属完了</span>
            </div>
            <p className="text-green-700">{result.message}</p>
          </div>

          {result.contract_number && (
            <div className="p-3 bg-gray-50 rounded-md mb-4">
              <p className="text-sm text-gray-500">契約番号</p>
              <p className="font-medium text-lg">{result.contract_number}</p>
            </div>
          )}

          {result.warnings && result.warnings.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md mb-4">
              <p className="font-medium text-yellow-800">注意事項:</p>
              <ul className="list-disc list-inside text-yellow-700">
                {result.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => {
                setCurrentStep(1)
                setSelectedEmployee(null)
                setSelectedFactory(null)
                setSuggestion(null)
                setResult(null)
                setEmployees([])
                setEmployeeSearch('')
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              新しい配属を作成
            </button>
            <button
              onClick={() => router.push(`/kobetsu/${result.contract_id}`)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              契約を表示
            </button>
            <button
              onClick={() => router.push('/kobetsu')}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              契約一覧へ
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
