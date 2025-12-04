'use client'

import { SkeletonStats, SkeletonTable } from '@/components/common/Skeleton'
import { employeeApi } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'

export default function EmployeesPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'resigned'>('all')
  const [companyFilter, setCompanyFilter] = useState<string>('')
  const [departmentFilter, setDepartmentFilter] = useState<string>('')
  const [lineFilter, setLineFilter] = useState<string>('')

  // Fetch employees
  const { data: employees = [], isLoading } = useQuery({
    queryKey: ['employees', search, statusFilter],
    queryFn: () => employeeApi.getList({
      search: search || undefined,
      status: statusFilter === 'all' ? undefined : statusFilter,
      limit: 500
    })
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['employeeStats'],
    queryFn: () => employeeApi.getStats()
  })

  // Extract unique filter options from employees
  const filterOptions = useMemo(() => {
    const companies = new Set<string>()
    const departments = new Set<string>()
    const lines = new Set<string>()

    employees.forEach((emp) => {
      if (emp.company_name) companies.add(emp.company_name)
      if (emp.department) departments.add(emp.department)
      if (emp.line_name) lines.add(emp.line_name)
    })

    return {
      companies: Array.from(companies).sort(),
      departments: Array.from(departments).sort(),
      lines: Array.from(lines).sort()
    }
  }, [employees])

  // Filter employees by company, department, line
  const filteredEmployees = useMemo(() => {
    return employees.filter((emp) => {
      if (companyFilter && emp.company_name !== companyFilter) return false
      if (departmentFilter && emp.department !== departmentFilter) return false
      if (lineFilter && emp.line_name !== lineFilter) return false
      return true
    })
  }, [employees, companyFilter, departmentFilter, lineFilter])

  // Reset dependent filters when parent changes
  const handleCompanyChange = (value: string) => {
    setCompanyFilter(value)
    setDepartmentFilter('')
    setLineFilter('')
  }

  const handleDepartmentChange = (value: string) => {
    setDepartmentFilter(value)
    setLineFilter('')
  }

  // Get filtered options based on current selections
  const filteredDepartments = useMemo(() => {
    if (!companyFilter) return filterOptions.departments
    const depts = new Set<string>()
    employees.forEach((emp) => {
      if (emp.company_name === companyFilter && emp.department) {
        depts.add(emp.department)
      }
    })
    return Array.from(depts).sort()
  }, [employees, companyFilter, filterOptions.departments])

  const filteredLines = useMemo(() => {
    const lines = new Set<string>()
    employees.forEach((emp) => {
      const matchCompany = !companyFilter || emp.company_name === companyFilter
      const matchDept = !departmentFilter || emp.department === departmentFilter
      if (matchCompany && matchDept && emp.line_name) {
        lines.add(emp.line_name)
      }
    })
    return Array.from(lines).sort()
  }, [employees, companyFilter, departmentFilter])

  // Clear all filters
  const clearFilters = () => {
    setCompanyFilter('')
    setDepartmentFilter('')
    setLineFilter('')
  }

  const handleRowClick = (employeeId: number) => {
    router.push(`/employees/${employeeId}`)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">従業員管理</h1>
          <p className="text-gray-600 mt-2">
            派遣社員の情報を確認・管理
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.push('/employees/create')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新規従業員
        </button>
      </div>

      {/* Stats Cards */}
      {isLoading ? (
        <SkeletonStats count={4} className="grid-cols-1 md:grid-cols-4 xl:grid-cols-4 mb-6" />
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">総従業員数</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {stats.total_employees}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">在籍中</p>
                <p className="text-3xl font-bold text-green-600 mt-1">
                  {stats.active_employees}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">退社済み</p>
                <p className="text-3xl font-bold text-gray-500 mt-1">
                  {stats.resigned_employees}
                </p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均年齢</p>
                <p className="text-3xl font-bold text-purple-600 mt-1">
                  {stats.average_age ? Math.round(stats.average_age) : 0}歳
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  18歳未満: {stats.under_18_count || 0} / 60歳以上: {stats.over_60_count || 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              検索
            </label>
            <input
              type="text"
              placeholder="社員番号、氏名で検索..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ステータス
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="ステータスフィルター"
            >
              <option value="all">すべて</option>
              <option value="active">在籍中</option>
              <option value="resigned">退社済み</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              派遣先
            </label>
            <select
              value={companyFilter}
              onChange={(e) => handleCompanyChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="派遣先フィルター"
            >
              <option value="">すべての派遣先</option>
              {filterOptions.companies.map((company) => (
                <option key={company} value={company}>{company}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              配属先
            </label>
            <select
              value={departmentFilter}
              onChange={(e) => handleDepartmentChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="配属先フィルター"
            >
              <option value="">すべての配属先</option>
              {filteredDepartments.map((dept) => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ライン
            </label>
            <select
              value={lineFilter}
              onChange={(e) => setLineFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="ラインフィルター"
            >
              <option value="">すべてのライン</option>
              {filteredLines.map((line) => (
                <option key={line} value={line}>{line}</option>
              ))}
            </select>
          </div>

          {/* Clear filters button */}
          {(companyFilter || departmentFilter || lineFilter) && (
            <div className="flex items-end">
              <button
                type="button"
                onClick={clearFilters}
                className="w-full px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                フィルターをクリア
              </button>
            </div>
          )}
        </div>

        {/* Active filters summary */}
        {(companyFilter || departmentFilter || lineFilter) && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm text-gray-500">絞り込み中:</span>
              {companyFilter && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                  派遣先: {companyFilter}
                  <button
                    type="button"
                    onClick={() => handleCompanyChange('')}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              )}
              {departmentFilter && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                  配属先: {departmentFilter}
                  <button
                    type="button"
                    onClick={() => handleDepartmentChange('')}
                    className="ml-2 text-green-600 hover:text-green-800"
                  >
                    ×
                  </button>
                </span>
              )}
              {lineFilter && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800">
                  ライン: {lineFilter}
                  <button
                    type="button"
                    onClick={() => setLineFilter('')}
                    className="ml-2 text-purple-600 hover:text-purple-800"
                  >
                    ×
                  </button>
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Employee List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <SkeletonTable rows={10} columns={10} />
        ) : filteredEmployees.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            従業員が見つかりません
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[100px]">
                    社員番号
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[120px]">
                    氏名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[80px]">
                    国籍
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[80px]">
                    年齢
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[80px]">
                    時給
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[80px]">
                    単価
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[120px]">
                    派遣先
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[100px]">
                    配属先
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[100px]">
                    配属ライン
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[120px]">
                    仕事内容
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider resize-x overflow-auto min-w-[100px]">
                    ステータス
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredEmployees.map((employee) => (
                  <tr
                    key={employee.id}
                    onClick={() => handleRowClick(employee.id)}
                    className="hover:bg-blue-50 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {employee.employee_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{employee.full_name_kanji}</div>
                      <div className="text-sm text-gray-500">{employee.full_name_kana}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.nationality}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.age}歳
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ¥{employee.hourly_rate ? Math.round(parseFloat(employee.hourly_rate)).toLocaleString(undefined, { maximumFractionDigits: 0 }) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ¥{employee.billing_rate ? Math.round(parseFloat(employee.billing_rate)).toLocaleString(undefined, { maximumFractionDigits: 0 }) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.company_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.department || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.line_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.position || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        employee.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {employee.status === 'active' ? '在籍中' : '退社済み'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="mt-4 text-sm text-gray-600 text-right">
        表示件数: {filteredEmployees.length}名
      </div>
    </div>
  )
}
