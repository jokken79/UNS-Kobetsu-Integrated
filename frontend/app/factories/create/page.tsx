'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { factoryApi } from '@/lib/api'
import type { FactoryCreate } from '@/types'
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'

export default function CreateFactoryPage() {
  const router = useRouter()
  const [formData, setFormData] = useState<Partial<FactoryCreate>>({
    is_active: true,
    break_minutes: 60,
  })

  const createMutation = useMutation({
    mutationFn: (data: FactoryCreate) => factoryApi.create(data),
    onSuccess: () => {
      alert('工場を作成しました')
      router.push('/factories')
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!formData.company_name || !formData.plant_name) {
      alert('会社名と工場名は必須です')
      return
    }

    createMutation.mutate(formData as FactoryCreate)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }))
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Breadcrumbs */}
        <Breadcrumbs
          items={[
            dashboardBreadcrumb,
            { label: '派遣先企業', href: '/factories' },
            { label: '新規作成' }
          ]}
          className="mb-6"
        />

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">新規工場登録</h1>
          <p className="text-gray-600 mt-2">
            派遣先企業・工場の基本情報を入力してください
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          {/* Company Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              企業情報 <span className="text-red-500">*必須</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  派遣先企業名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 株式会社サンプル"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  企業住所
                </label>
                <input
                  type="text"
                  name="company_address"
                  value={formData.company_address || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 東京都渋谷区..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  企業電話番号
                </label>
                <input
                  type="tel"
                  name="company_phone"
                  value={formData.company_phone || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 03-1234-5678"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  FAX番号
                </label>
                <input
                  type="tel"
                  name="company_fax"
                  value={formData.company_fax || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 03-1234-5679"
                />
              </div>
            </div>
          </div>

          {/* Plant Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              工場情報 <span className="text-red-500">*必須</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="plant_name"
                  value={formData.plant_name || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 本社工場"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場住所
                </label>
                <input
                  type="text"
                  name="plant_address"
                  value={formData.plant_address || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 愛知県豊田市..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場電話番号
                </label>
                <input
                  type="tel"
                  name="plant_phone"
                  value={formData.plant_phone || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 0565-12-3456"
                />
              </div>
            </div>
          </div>

          {/* Responsible Person */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              派遣先責任者
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  部署名
                </label>
                <input
                  type="text"
                  name="client_responsible_department"
                  value={formData.client_responsible_department || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 総務部"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  担当者名
                </label>
                <input
                  type="text"
                  name="client_responsible_name"
                  value={formData.client_responsible_name || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 山田太郎"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  連絡先電話番号
                </label>
                <input
                  type="tel"
                  name="client_responsible_phone"
                  value={formData.client_responsible_phone || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 090-1234-5678"
                />
              </div>
            </div>
          </div>

          {/* Work Schedule */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              就業スケジュール
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  就業時間説明
                </label>
                <textarea
                  name="work_hours_description"
                  value={formData.work_hours_description || ''}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 日勤 8:00-17:00、夜勤 20:00-5:00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  休憩時間（分）
                </label>
                <input
                  type="number"
                  name="break_minutes"
                  value={formData.break_minutes || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例: 60"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  抵触日
                </label>
                <input
                  type="date"
                  name="conflict_date"
                  value={formData.conflict_date || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="その他メモ..."
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
            >
              {createMutation.isPending ? '作成中...' : '工場を作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
