'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { employeeApi, factoryApi } from '@/lib/api'
import FactoryCascadeSelector from '@/components/factory/FactoryCascadeSelector'
import type { EmployeeUpdate, FactoryCascadeData } from '@/types'

export default function EditEmployeePage() {
  const router = useRouter()
  const params = useParams()
  const queryClient = useQueryClient()
  const employeeId = parseInt(params.id as string)

  const [formData, setFormData] = useState<Partial<EmployeeUpdate>>({})
  const [isEditing, setIsEditing] = useState(false)
  const [isEditingAssignment, setIsEditingAssignment] = useState(false)
  const [selectedFactory, setSelectedFactory] = useState<FactoryCascadeData | null>(null)

  // Fetch employee data
  const { data: employee, isLoading } = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => employeeApi.getById(employeeId),
  })

  // Update formData when employee data loads
  useEffect(() => {
    if (employee) {
      setFormData({
        full_name_kanji: employee.full_name_kanji,
        full_name_kana: employee.full_name_kana,
        full_name_romaji: employee.full_name_romaji,
        gender: employee.gender,
        date_of_birth: employee.date_of_birth,
        nationality: employee.nationality,
        phone: employee.phone,
        mobile: employee.mobile,
        email: employee.email,
        address: employee.address,
        status: employee.status,
        hourly_rate: employee.hourly_rate,
        billing_rate: employee.billing_rate,
        visa_type: employee.visa_type,
        visa_expiry_date: employee.visa_expiry_date,
        notes: employee.notes,
      })
    }
  }, [employee])

  const updateMutation = useMutation({
    mutationFn: (data: EmployeeUpdate) => employeeApi.update(employeeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employee', employeeId] })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      alert('従業員情報を更新しました')
      setIsEditing(false)
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => employeeApi.delete(employeeId),
    onSuccess: () => {
      alert('従業員を削除しました（退社済みに変更）')
      router.push('/employees')
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation for assigning employee to factory/line
  const assignMutation = useMutation({
    mutationFn: async (data: { factory_id: number; factory_line_id?: number; company_name?: string; plant_name?: string; department?: string; line_name?: string }) => {
      // Use the update endpoint to set assignment
      return employeeApi.update(employeeId, {
        factory_id: data.factory_id,
        factory_line_id: data.factory_line_id,
        company_name: data.company_name,
        plant_name: data.plant_name,
        department: data.department,
        line_name: data.line_name,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employee', employeeId] })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      alert('派遣先を更新しました')
      setIsEditingAssignment(false)
      setSelectedFactory(null)
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Handle factory selection
  const handleFactorySelect = (data: FactoryCascadeData) => {
    setSelectedFactory(data)
  }

  // Save assignment
  const handleSaveAssignment = () => {
    if (!selectedFactory) return

    assignMutation.mutate({
      factory_id: selectedFactory.factory.id,
      factory_line_id: selectedFactory.line.id,
      company_name: selectedFactory.factory.company_name,
      plant_name: selectedFactory.factory.plant_name,
      department: selectedFactory.line.department,
      line_name: selectedFactory.line.line_name,
    })
  }

  // Clear assignment
  const handleClearAssignment = () => {
    if (!confirm('派遣先の設定を解除しますか？')) return

    assignMutation.mutate({
      factory_id: undefined as any,
      factory_line_id: undefined as any,
      company_name: undefined,
      plant_name: undefined,
      department: undefined,
      line_name: undefined,
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData as EmployeeUpdate)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }))
  }

  const handleDelete = () => {
    if (confirm('本当にこの従業員を削除しますか？（退社済みに変更されます）')) {
      deleteMutation.mutate()
    }
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

  if (!employee) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600">従業員が見つかりません</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">従業員情報</h1>
            <p className="text-gray-600 mt-2">
              社員番号: {employee.employee_number}
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
                  // Reset form data
                  setFormData({
                    full_name_kanji: employee.full_name_kanji,
                    full_name_kana: employee.full_name_kana,
                    status: employee.status,
                    // ... other fields
                  })
                }}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                キャンセル
              </button>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          {/* Basic Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              基本情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  氏名（漢字）
                </label>
                <input
                  type="text"
                  name="full_name_kanji"
                  value={formData.full_name_kanji || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  氏名（カナ）
                </label>
                <input
                  type="text"
                  name="full_name_kana"
                  value={formData.full_name_kana || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  性別
                </label>
                <select
                  name="gender"
                  value={formData.gender || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  aria-label="性別"
                >
                  <option value="">選択してください</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  生年月日
                </label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={formData.date_of_birth || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  国籍
                </label>
                <input
                  type="text"
                  name="nationality"
                  value={formData.nationality || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ステータス
                </label>
                <select
                  name="status"
                  value={formData.status || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  aria-label="ステータス"
                >
                  <option value="active">在籍中</option>
                  <option value="resigned">退社済み</option>
                  <option value="on_leave">休職</option>
                </select>
              </div>
            </div>
          </div>

          {/* Contact Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              連絡先
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  電話番号
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  携帯電話
                </label>
                <input
                  type="tel"
                  name="mobile"
                  value={formData.mobile || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  メールアドレス
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  住所
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* 派遣先情報 (Assignment) */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                派遣先情報
              </h2>
              {!isEditingAssignment && (
                <button
                  type="button"
                  onClick={() => setIsEditingAssignment(true)}
                  className="px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                >
                  変更
                </button>
              )}
            </div>

            {!isEditingAssignment ? (
              // Display current assignment
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    派遣先
                  </label>
                  <p className="px-4 py-2 bg-gray-100 rounded-lg text-gray-900">
                    {employee.company_name || '未設定'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    工場
                  </label>
                  <p className="px-4 py-2 bg-gray-100 rounded-lg text-gray-900">
                    {employee.plant_name || '未設定'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    配属先
                  </label>
                  <p className="px-4 py-2 bg-gray-100 rounded-lg text-gray-900">
                    {employee.department || '未設定'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ライン
                  </label>
                  <p className="px-4 py-2 bg-gray-100 rounded-lg text-gray-900">
                    {employee.line_name || '未設定'}
                  </p>
                </div>
              </div>
            ) : (
              // Edit assignment
              <div className="space-y-4">
                <FactoryCascadeSelector
                  onSelect={handleFactorySelect}
                  className="mb-4"
                />

                {selectedFactory && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800 font-medium mb-2">選択中:</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">派遣先:</span>{' '}
                        <span className="font-medium">{selectedFactory.factory.company_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">工場:</span>{' '}
                        <span className="font-medium">{selectedFactory.factory.plant_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">配属先:</span>{' '}
                        <span className="font-medium">{selectedFactory.line.department || '-'}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">ライン:</span>{' '}
                        <span className="font-medium">{selectedFactory.line.line_name || '-'}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSaveAssignment}
                    disabled={!selectedFactory || assignMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
                  >
                    {assignMutation.isPending ? '保存中...' : '保存'}
                  </button>
                  {employee.factory_id && (
                    <button
                      type="button"
                      onClick={handleClearAssignment}
                      disabled={assignMutation.isPending}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:bg-gray-400"
                    >
                      解除
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingAssignment(false)
                      setSelectedFactory(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    キャンセル
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Employment Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              雇用情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  時給
                </label>
                <input
                  type="number"
                  name="hourly_rate"
                  value={formData.hourly_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  請求単価
                </label>
                <input
                  type="number"
                  name="billing_rate"
                  value={formData.billing_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Visa Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              在留資格
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  在留資格
                </label>
                <input
                  type="text"
                  name="visa_type"
                  value={formData.visa_type || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  在留期限
                </label>
                <input
                  type="date"
                  name="visa_expiry_date"
                  value={formData.visa_expiry_date || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              備考
            </label>
            <textarea
              name="notes"
              value={formData.notes || ''}
              onChange={handleChange}
              rows={4}
              disabled={!isEditing}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
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
      </div>
    </div>
  )
}
