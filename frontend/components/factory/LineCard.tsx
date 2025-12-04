'use client'

import { useConfirmActions } from '@/components/common/ConfirmContext'
import { cn, formatCurrency, formatDate } from '@/lib/utils'
import type { EmployeeResponse, FactoryLineResponse } from '@/types'
import { useState } from 'react'

interface LineCardProps {
  line: FactoryLineResponse
  employees: EmployeeResponse[]  // Employees assigned to this line
  baseRate?: number              // Factory line's base hourly_rate
  onEdit: (lineId: number) => void
  onDelete: (lineId: number) => void
  isExpanded?: boolean
  onToggleExpand?: () => void
}

export function LineCard({
  line,
  employees,
  baseRate,
  onEdit,
  onDelete,
  isExpanded: controlledExpanded,
  onToggleExpand
}: LineCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(true)
  const { confirmDelete } = useConfirmActions()

  // Use controlled expansion if provided, otherwise use internal state
  const isExpanded = controlledExpanded !== undefined ? controlledExpanded : internalExpanded

  const handleToggleExpand = () => {
    if (onToggleExpand) {
      onToggleExpand()
    } else {
      setInternalExpanded(!internalExpanded)
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    console.log('Delete button clicked for line', line.id)

    const confirmed = await confirmDelete(
      `${line.department ? `${line.department} / ` : ''}${line.line_name || 'ライン'}`
    )
    console.log('Confirmed?', confirmed)

    if (confirmed) {
      console.log('Calling onDelete with line.id', line.id)
      onDelete(line.id)
    }
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit(line.id)
  }

  // Sort employees by hourly_rate DESC (highest paid first)
  const sortedEmployees = [...employees].sort((a, b) => {
    const rateA = a.hourly_rate || line.hourly_rate || 0
    const rateB = b.hourly_rate || line.hourly_rate || 0
    return rateB - rateA
  })

  // Determine base rate to use for comparison
  const comparisonRate = baseRate || line.hourly_rate || 0

  return (
    <div className="bg-white rounded-lg border border-purple-200 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div
        className="px-6 py-4 border-b border-purple-100 cursor-pointer select-none hover:bg-purple-50/50 transition-colors"
        onClick={handleToggleExpand}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Expand/Collapse Icon */}
            <button
              className="text-purple-600 hover:text-purple-700 transition-colors"
              onClick={(e) => {
                e.stopPropagation()
                handleToggleExpand()
              }}
            >
              <svg
                className={cn(
                  'w-5 h-5 transition-transform duration-200',
                  isExpanded && 'rotate-90'
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>

            {/* Line Name */}
            <div className="flex items-center gap-2">
              <span className="text-xl">🏭</span>
              <h3 className="text-lg font-semibold text-gray-900">
                {line.department && `${line.department} / `}
                {line.line_name || 'ライン'}
              </h3>
              {employees.length > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {employees.length}名
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleEdit}
              className="px-3 py-1.5 text-sm font-medium text-purple-700 hover:text-purple-800 hover:bg-purple-100 rounded-md transition-colors"
            >
              編集
            </button>
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
            >
              削除
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-6 space-y-6">
          {/* Top Row: Supervisor and Base Rates */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Supervisor Info */}
            {(line.supervisor_name || line.supervisor_department) && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">👤</span>
                  <h4 className="font-medium text-gray-900">指揮命令者</h4>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  {line.supervisor_department && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">部署:</span>
                      <span className="text-gray-900">{line.supervisor_department}</span>
                    </div>
                  )}
                  {line.supervisor_position && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">役職:</span>
                      <span className="text-gray-900">{line.supervisor_position}</span>
                    </div>
                  )}
                  {line.supervisor_name && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">氏名:</span>
                      <span className="text-gray-900">{line.supervisor_name}</span>
                    </div>
                  )}
                  {line.supervisor_phone && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">電話:</span>
                      <span className="text-gray-900">{line.supervisor_phone}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Line Base Rates */}
            {(line.hourly_rate || line.billing_rate || line.overtime_rate) && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">💰</span>
                  <h4 className="font-medium text-gray-900">ライン基本単価</h4>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 space-y-2">
                  {line.hourly_rate && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">時給:</span>
                      <span className="text-gray-900 font-medium">{formatCurrency(line.hourly_rate)}</span>
                    </div>
                  )}
                  {line.billing_rate && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">請求:</span>
                      <span className="text-gray-900 font-medium">{formatCurrency(line.billing_rate)}</span>
                    </div>
                  )}
                  {line.overtime_rate && (
                    <div className="flex">
                      <span className="text-gray-600 min-w-[4rem]">残業:</span>
                      <span className="text-gray-900 font-medium">{formatCurrency(line.overtime_rate)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Job Description */}
          {line.job_description && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">📋</span>
                <h4 className="font-medium text-gray-900">業務内容</h4>
              </div>
              <p className="text-gray-700 bg-gray-50 rounded-lg p-4">
                {line.job_description}
              </p>
              {line.job_description_detail && (
                <p className="text-gray-600 mt-2 text-sm bg-gray-50 rounded-lg p-4">
                  {line.job_description_detail}
                </p>
              )}
            </div>
          )}

          {/* Employee Table */}
          {sortedEmployees.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">👥</span>
                <h4 className="font-medium text-gray-900">配属社員 ({sortedEmployees.length}名)</h4>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <thead className="bg-purple-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        社員番号
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        氏名
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                        時給
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                        請求単価
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        入社日
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {sortedEmployees.map((employee, index) => {
                      const employeeRate = employee.hourly_rate || comparisonRate
                      const isAboveBase = employee.hourly_rate && comparisonRate && employee.hourly_rate > comparisonRate

                      return (
                        <tr
                          key={employee.id}
                          className={cn(
                            'hover:bg-gray-50 transition-colors',
                            index % 2 === 1 && 'bg-gray-50/50'
                          )}
                        >
                          <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                            {employee.employee_number}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {employee.display_name || employee.full_name_kana || employee.full_name_kanji}
                          </td>
                          <td className="px-4 py-3 text-sm text-right">
                            <span className={cn(
                              'font-medium',
                              employee.hourly_rate ? 'text-gray-900' : 'text-gray-500'
                            )}>
                              {formatCurrency(employeeRate)}
                            </span>
                            {isAboveBase && (
                              <span className="ml-1 text-green-600 font-bold" title="基本単価より高い">
                                ↑
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-right">
                            <span className={cn(
                              'font-medium',
                              employee.billing_rate ? 'text-gray-900' : 'text-gray-500'
                            )}>
                              {employee.billing_rate ? formatCurrency(employee.billing_rate) : '-'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {employee.hire_date ? formatDate(employee.hire_date) : '-'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              {/* Footer note */}
              <div className="mt-2 text-right text-xs text-gray-500">
                ↑ = 基本単価より高い時給
              </div>
            </div>
          )}

          {/* Empty State */}
          {sortedEmployees.length === 0 && (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <span className="text-4xl mb-3 block">👥</span>
              <p className="text-gray-600">このラインに配属されている社員はいません</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}