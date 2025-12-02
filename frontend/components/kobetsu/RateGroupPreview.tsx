'use client'

import { useState, useEffect, useRef } from 'react'
import {
  CurrencyYenIcon,
  ExclamationTriangleIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'

// Types
interface RateGroup {
  hourly_rate: number
  billing_rate?: number
  employee_count: number
  employees: EmployeeInGroup[]
}

interface EmployeeInGroup {
  id: number
  employee_number: string
  full_name_kana: string
  full_name_kanji?: string
  hourly_rate?: number
  billing_rate?: number
  department?: string
  line_name?: string
}

interface RateGroupPreviewProps {
  groups: RateGroup[]
  totalEmployees: number
  hasMultipleRates: boolean
  suggestedContracts: number
  message: string
  onConfirm: (splitByRate: boolean) => void
  onCancel: () => void
  isLoading?: boolean
}

export function RateGroupPreview({
  groups,
  totalEmployees,
  hasMultipleRates,
  suggestedContracts,
  message,
  onConfirm,
  onCancel,
  isLoading = false
}: RateGroupPreviewProps) {
  const [splitByRate, setSplitByRate] = useState(hasMultipleRates)
  const confirmButtonRef = useRef<HTMLButtonElement>(null)

  // Focus management and keyboard shortcuts
  useEffect(() => {
    // Focus confirm button when dialog opens
    setTimeout(() => {
      confirmButtonRef.current?.focus()
    }, 50)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      } else if (e.key === 'Enter' && e.ctrlKey) {
        handleConfirm()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [onCancel])

  const handleConfirm = () => {
    onConfirm(splitByRate)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY'
    }).format(value)
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-gray-500 bg-opacity-75 backdrop-blur-sm transition-opacity z-40"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all w-full max-w-4xl animate-fade-in-up">
          {/* Header */}
          <div className="bg-white px-4 pt-5 sm:px-6">
            <div className="flex items-center gap-2 mb-4">
              <UserGroupIcon className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                単価別グループプレビュー
              </h2>
            </div>

            {/* Warning Banner */}
            {hasMultipleRates && (
              <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-md">
                <div className="flex items-start">
                  <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 mt-0.5 mr-2" />
                  <div className="flex-1">
                    <p className="text-sm text-amber-800 font-medium">
                      {message || `${totalEmployees}名を${suggestedContracts}つの契約に分割することを推奨します`}
                    </p>
                    <p className="text-sm text-amber-700 mt-1">
                      従業員の時給単価が異なるため、別々の契約として作成することをお勧めします。
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="px-4 py-4 sm:px-6 max-h-[60vh] overflow-y-auto">
            {groups.map((group, index) => (
              <div key={index} className="mb-6 last:mb-0">
                {/* Group Header */}
                <div className="bg-gradient-to-r from-purple-50 to-white p-4 rounded-t-lg border border-purple-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CurrencyYenIcon className="h-5 w-5 text-green-600" />
                      <span className="text-lg font-semibold text-gray-900">
                        契約 #{index + 1}: {formatCurrency(group.hourly_rate)}
                      </span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                        {group.employee_count}名
                      </span>
                    </div>
                    {group.billing_rate && (
                      <span className="text-sm text-gray-600">
                        請求単価: {formatCurrency(group.billing_rate)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Employee Table */}
                <div className="border border-t-0 border-purple-200 rounded-b-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          社員番号
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          氏名
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          配属先
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ライン
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {group.employees.map((employee) => (
                        <tr key={employee.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                            {employee.employee_number}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                            <div>
                              <div className="font-medium">{employee.full_name_kanji || employee.full_name_kana}</div>
                              {employee.full_name_kanji && (
                                <div className="text-xs text-gray-500">{employee.full_name_kana}</div>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600">
                            {employee.department || '-'}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600">
                            {employee.line_name || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          {/* Options Section */}
          {hasMultipleRates && (
            <div className="px-4 py-4 sm:px-6 border-t border-gray-200">
              <div className="space-y-3">
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="radio"
                    name="contractOption"
                    value="single"
                    checked={!splitByRate}
                    onChange={() => setSplitByRate(false)}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700 group-hover:text-gray-900">
                    1つの契約として作成（全員同じ単価を適用）
                  </span>
                </label>
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="radio"
                    name="contractOption"
                    value="split"
                    checked={splitByRate}
                    onChange={() => setSplitByRate(true)}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700 group-hover:text-gray-900">
                    {suggestedContracts}つの契約に分割して作成（推奨）
                  </span>
                </label>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
            <button
              ref={confirmButtonRef}
              type="button"
              className="inline-flex w-full justify-center rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-700 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              onClick={handleConfirm}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></span>
                  処理中...
                </span>
              ) : (
                '契約を作成'
              )}
            </button>
            <button
              type="button"
              className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              onClick={onCancel}
              disabled={isLoading}
            >
              キャンセル
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// Add custom animation to global styles if not exists
if (typeof document !== 'undefined' && !document.getElementById('rate-group-preview-animations')) {
  const style = document.createElement('style')
  style.id = 'rate-group-preview-animations'
  style.innerHTML = `
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translate3d(0, 10%, 0);
      }
      to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
      }
    }

    .animate-fade-in-up {
      animation: fadeInUp 0.3s ease-out;
    }
  `
  document.head.appendChild(style)
}