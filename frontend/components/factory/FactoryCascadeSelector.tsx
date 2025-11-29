'use client'

/**
 * FactoryCascadeSelector - Cascading dropdown for factory selection
 *
 * Flow: 派遣先 → 工場名 → 配属先 → ライン
 *
 * When a line is selected, populates the form with factory data.
 */

import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { factoryApi } from '@/lib/api'
import type {
  CompanyOption,
  PlantOption,
  DepartmentOption,
  LineOption,
  FactoryCascadeData,
} from '@/types'

interface FactoryCascadeSelectorProps {
  onSelect: (data: FactoryCascadeData) => void
  initialFactoryId?: number
  initialLineId?: number
  disabled?: boolean
  className?: string
}

export default function FactoryCascadeSelector({
  onSelect,
  initialFactoryId,
  initialLineId,
  disabled = false,
  className = '',
}: FactoryCascadeSelectorProps) {
  // Selected values
  const [selectedCompany, setSelectedCompany] = useState<string>('')
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(initialFactoryId || null)
  const [selectedDepartment, setSelectedDepartment] = useState<string>('')
  const [selectedLineId, setSelectedLineId] = useState<number | null>(initialLineId || null)

  // Fetch companies (派遣先)
  const { data: companies = [], isLoading: loadingCompanies } = useQuery({
    queryKey: ['factory-companies'],
    queryFn: () => factoryApi.getCompanies(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch plants (工場名) when company is selected
  const { data: plants = [], isLoading: loadingPlants } = useQuery({
    queryKey: ['factory-plants', selectedCompany],
    queryFn: () => factoryApi.getPlants(selectedCompany),
    enabled: !!selectedCompany,
    staleTime: 5 * 60 * 1000,
  })

  // Fetch departments (配属先) when factory is selected
  const { data: departments = [], isLoading: loadingDepartments } = useQuery({
    queryKey: ['factory-departments', selectedFactoryId],
    queryFn: () => factoryApi.getDepartments(selectedFactoryId!),
    enabled: !!selectedFactoryId,
    staleTime: 5 * 60 * 1000,
  })

  // Fetch lines (ライン) when factory/department is selected
  const { data: lines = [], isLoading: loadingLines } = useQuery({
    queryKey: ['factory-lines', selectedFactoryId, selectedDepartment],
    queryFn: () => factoryApi.getLines(selectedFactoryId!, selectedDepartment || undefined),
    enabled: !!selectedFactoryId,
    staleTime: 5 * 60 * 1000,
  })

  // Handle company change
  const handleCompanyChange = useCallback((company: string) => {
    setSelectedCompany(company)
    setSelectedFactoryId(null)
    setSelectedDepartment('')
    setSelectedLineId(null)
  }, [])

  // Handle plant/factory change
  const handleFactoryChange = useCallback((factoryId: number) => {
    setSelectedFactoryId(factoryId)
    setSelectedDepartment('')
    setSelectedLineId(null)
  }, [])

  // Handle department change
  const handleDepartmentChange = useCallback((department: string) => {
    setSelectedDepartment(department)
    setSelectedLineId(null)
  }, [])

  // Handle line selection - fetch cascade data and notify parent
  const handleLineChange = useCallback(async (lineId: number) => {
    setSelectedLineId(lineId)

    try {
      const cascadeData = await factoryApi.getCascadeData(lineId)
      onSelect(cascadeData)
    } catch (error) {
      // Failed to fetch cascade data - error handled silently
    }
  }, [onSelect])

  // Load initial data if provided
  useEffect(() => {
    if (initialLineId) {
      factoryApi.getCascadeData(initialLineId).then((data) => {
        setSelectedCompany(data.factory.company_name)
        setSelectedFactoryId(data.factory.id)
        setSelectedDepartment(data.line.department || '')
        setSelectedLineId(data.line.id)
      }).catch(() => {
        // Failed to load initial cascade data - error handled silently
      })
    }
  }, [initialLineId])

  const selectClassName = `
    w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
    disabled:bg-gray-100 disabled:cursor-not-allowed
  `

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 派遣先 (Company) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          派遣先 <span className="text-red-500">*</span>
        </label>
        <select
          value={selectedCompany}
          onChange={(e) => handleCompanyChange(e.target.value)}
          disabled={disabled || loadingCompanies}
          className={selectClassName}
        >
          <option value="">派遣先を選択...</option>
          {companies.map((company) => (
            <option key={company.company_name} value={company.company_name}>
              {company.company_name} ({company.factories_count} 工場)
            </option>
          ))}
        </select>
        {loadingCompanies && (
          <span className="text-sm text-gray-500 ml-2">読み込み中...</span>
        )}
      </div>

      {/* 工場名 (Plant) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          工場名 <span className="text-red-500">*</span>
        </label>
        <select
          value={selectedFactoryId || ''}
          onChange={(e) => handleFactoryChange(Number(e.target.value))}
          disabled={disabled || !selectedCompany || loadingPlants}
          className={selectClassName}
        >
          <option value="">工場を選択...</option>
          {plants.map((plant) => (
            <option key={plant.id} value={plant.id}>
              {plant.plant_name}
              {plant.plant_address && ` - ${plant.plant_address}`}
            </option>
          ))}
        </select>
        {loadingPlants && (
          <span className="text-sm text-gray-500 ml-2">読み込み中...</span>
        )}
      </div>

      {/* 配属先 (Department) - Optional */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          配属先
        </label>
        <select
          value={selectedDepartment}
          onChange={(e) => handleDepartmentChange(e.target.value)}
          disabled={disabled || !selectedFactoryId || loadingDepartments}
          className={selectClassName}
        >
          <option value="">全配属先</option>
          {departments.map((dept) => (
            <option key={dept.department} value={dept.department}>
              {dept.department} ({dept.lines_count} ライン)
            </option>
          ))}
        </select>
        {loadingDepartments && (
          <span className="text-sm text-gray-500 ml-2">読み込み中...</span>
        )}
      </div>

      {/* ライン (Line) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          ライン <span className="text-red-500">*</span>
        </label>
        <select
          value={selectedLineId || ''}
          onChange={(e) => handleLineChange(Number(e.target.value))}
          disabled={disabled || !selectedFactoryId || loadingLines}
          className={selectClassName}
        >
          <option value="">ラインを選択...</option>
          {lines.map((line) => (
            <option key={line.id} value={line.id}>
              {line.line_name || 'デフォルト'}
              {line.job_description && ` - ${line.job_description}`}
              {line.hourly_rate && ` (¥${line.hourly_rate})`}
            </option>
          ))}
        </select>
        {loadingLines && (
          <span className="text-sm text-gray-500 ml-2">読み込み中...</span>
        )}
      </div>

      {/* Selected line info */}
      {selectedLineId && (
        <div className="p-3 bg-blue-50 rounded-md border border-blue-200">
          <p className="text-sm text-blue-800">
            選択中: {selectedCompany} → {plants.find(p => p.id === selectedFactoryId)?.plant_name}
            {selectedDepartment && ` → ${selectedDepartment}`}
            → {lines.find(l => l.id === selectedLineId)?.line_name || 'デフォルト'}
          </p>
        </div>
      )}
    </div>
  )
}
