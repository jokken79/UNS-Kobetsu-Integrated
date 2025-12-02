'use client'

import { useState, useEffect } from 'react'
import { useFactory, useUpdateFactory, useDeleteFactory } from '@/hooks/useFactories'
import { useToastActions } from '@/components/common/ToastContext'
import { useConfirmActions } from '@/components/common/ConfirmContext'
import type { FactoryUpdate } from '@/types'

interface FactoryDetailProps {
  factoryId: number | null
  onSave?: () => void
  onDelete?: () => void
}

export function FactoryDetail({ factoryId, onSave, onDelete }: FactoryDetailProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<FactoryUpdate>({})
  const [isAddingLine, setIsAddingLine] = useState(false)

  // Hooks
  const { data: factory, isLoading, error } = useFactory(factoryId)
  const updateMutation = useUpdateFactory(factoryId!)
  const deleteMutation = useDeleteFactory()
  const toast = useToastActions()
  const { confirmDelete } = useConfirmActions()

  // Reset form when factory data changes
  useEffect(() => {
    if (factory) {
      setFormData({
        company_name: factory.company_name,
        company_address: factory.company_address,
        company_phone: factory.company_phone,
        plant_name: factory.plant_name,
        plant_address: factory.plant_address,
        plant_phone: factory.plant_phone,
        client_responsible_department: factory.client_responsible_department,
        client_responsible_name: factory.client_responsible_name,
        client_responsible_phone: factory.client_responsible_phone,
        client_complaint_department: factory.client_complaint_department,
        client_complaint_name: factory.client_complaint_name,
        client_complaint_phone: factory.client_complaint_phone,
        conflict_date: factory.conflict_date,
        break_minutes: factory.break_minutes,
      })
    }
  }, [factory])

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setIsAddingLine(false)
    // Reset form to original data
    if (factory) {
      setFormData({
        company_name: factory.company_name,
        company_address: factory.company_address,
        company_phone: factory.company_phone,
        plant_name: factory.plant_name,
        plant_address: factory.plant_address,
        plant_phone: factory.plant_phone,
        client_responsible_department: factory.client_responsible_department,
        client_responsible_name: factory.client_responsible_name,
        client_responsible_phone: factory.client_responsible_phone,
        client_complaint_department: factory.client_complaint_department,
        client_complaint_name: factory.client_complaint_name,
        client_complaint_phone: factory.client_complaint_phone,
        conflict_date: factory.conflict_date,
        break_minutes: factory.break_minutes,
      })
    }
  }

  const handleSave = async () => {
    if (!factoryId) return

    try {
      await updateMutation.mutateAsync(formData)
      toast.success('工場情報を更新しました')
      setIsEditing(false)
      onSave?.()
    } catch (error) {
      console.error('Failed to update factory:', error)
      toast.error('更新に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!factoryId || !factory) return

    const confirmed = await confirmDelete(
      `${factory.company_name} - ${factory.plant_name}`
    )

    if (confirmed) {
      try {
        await deleteMutation.mutateAsync(factoryId)
        toast.success('工場を削除しました')
        onDelete?.()
      } catch (error) {
        console.error('Failed to delete factory:', error)
        toast.error('削除に失敗しました')
      }
    }
  }

  const handleFieldChange = (field: keyof FactoryUpdate, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-600">
          工場情報の読み込みに失敗しました
        </div>
      </div>
    )
  }

  // No selection state
  if (!factoryId || !factory) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-gray-500 text-center py-12">
          左側から工場を選択してください
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏢</span>
            <h2 className="text-xl font-semibold">
              {factory.company_name} - {factory.plant_name}
            </h2>
          </div>
          {!isEditing && (
            <div className="flex gap-2">
              <button
                onClick={handleEdit}
                className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                編集
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                削除
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Company & Factory Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Company Info Card */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">📋</span>
              <h3 className="font-semibold">会社情報</h3>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-sm text-gray-600">会社名</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.company_name || ''}
                    onChange={(e) => handleFieldChange('company_name', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.company_name}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">住所</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.company_address || ''}
                    onChange={(e) => handleFieldChange('company_address', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.company_address || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">電話</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.company_phone || ''}
                    onChange={(e) => handleFieldChange('company_phone', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.company_phone || '-'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Factory Info Card */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">📍</span>
              <h3 className="font-semibold">工場情報</h3>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-sm text-gray-600">工場名</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.plant_name || ''}
                    onChange={(e) => handleFieldChange('plant_name', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.plant_name}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">住所</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.plant_address || ''}
                    onChange={(e) => handleFieldChange('plant_address', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.plant_address || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">電話</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.plant_phone || ''}
                    onChange={(e) => handleFieldChange('plant_phone', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.plant_phone || '-'}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Responsible Persons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Dispatch Responsible Card */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">👤</span>
              <h3 className="font-semibold">派遣先責任者</h3>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-sm text-gray-600">部署</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_responsible_department || ''}
                    onChange={(e) => handleFieldChange('client_responsible_department', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_responsible_department || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">氏名</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_responsible_name || ''}
                    onChange={(e) => handleFieldChange('client_responsible_name', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_responsible_name || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">電話</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_responsible_phone || ''}
                    onChange={(e) => handleFieldChange('client_responsible_phone', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_responsible_phone || '-'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Complaint Contact Card */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">📞</span>
              <h3 className="font-semibold">派遣先苦情担当</h3>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-sm text-gray-600">部署</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_complaint_department || ''}
                    onChange={(e) => handleFieldChange('client_complaint_department', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_complaint_department || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">氏名</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_complaint_name || ''}
                    onChange={(e) => handleFieldChange('client_complaint_name', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_complaint_name || '-'}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-600">電話</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.client_complaint_phone || ''}
                    onChange={(e) => handleFieldChange('client_complaint_phone', e.target.value)}
                    className="form-input w-full"
                  />
                ) : (
                  <p className="font-medium">{factory.client_complaint_phone || '-'}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Other Info */}
        <div className="flex flex-wrap gap-6">
          <div>
            <span className="text-sm text-gray-600">📅 抵触日:</span>
            {isEditing ? (
              <input
                type="date"
                value={formData.conflict_date || ''}
                onChange={(e) => handleFieldChange('conflict_date', e.target.value)}
                className="form-input ml-2"
              />
            ) : (
              <span className="font-medium ml-2">
                {factory.conflict_date ?
                  new Date(factory.conflict_date).toLocaleDateString('ja-JP') :
                  '未設定'
                }
              </span>
            )}
          </div>
          <div>
            <span className="text-sm text-gray-600">⏰ 休憩:</span>
            {isEditing ? (
              <input
                type="number"
                value={formData.break_minutes || 0}
                onChange={(e) => handleFieldChange('break_minutes', parseInt(e.target.value))}
                className="form-input ml-2 w-20"
                min="0"
              />
            ) : (
              <span className="font-medium ml-2">{factory.break_minutes || 0}分</span>
            )}
          </div>
        </div>

        {/* Production Lines Section */}
        <div className="border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">
              生産ライン ({factory.lines?.length || 0})
            </h3>
            {!isEditing && (
              <button
                onClick={() => setIsAddingLine(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + ライン追加
              </button>
            )}
          </div>

          {/* LineCard components would be rendered here */}
          <div className="space-y-3">
            {factory.lines?.map(line => (
              <div
                key={line.id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">
                      {line.department && `${line.department} - `}
                      {line.line_name || 'ライン名未設定'}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {line.job_description || '仕事内容未設定'}
                    </div>
                    <div className="text-sm text-gray-500 mt-2">
                      責任者: {line.supervisor_name || '未設定'} |
                      時給: ¥{line.hourly_rate?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    line.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {line.is_active ? '有効' : '無効'}
                  </div>
                </div>
              </div>
            ))}
            {(!factory.lines || factory.lines.length === 0) && (
              <div className="text-gray-500 text-center py-8">
                生産ラインが登録されていません
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {isEditing && (
          <div className="border-t pt-6 flex justify-end gap-3">
            <button
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={updateMutation.isPending}
            >
              キャンセル
            </button>
            <button
              onClick={handleSave}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <>
                  <span className="animate-spin">⏳</span>
                  保存中...
                </>
              ) : (
                <>
                  💾 保存する
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}