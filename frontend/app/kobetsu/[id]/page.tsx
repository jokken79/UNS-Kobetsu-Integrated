'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { kobetsuApi } from '@/lib/api'
import { StatusBadge } from '@/components/kobetsu/StatusBadge'
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'

export default function KobetsuDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const id = Number(params.id)

  const { data: contract, isLoading, error } = useQuery({
    queryKey: ['kobetsu', id],
    queryFn: () => kobetsuApi.getById(id),
    enabled: !!id,
  })

  // 従業員詳細（単価情報含む）
  const { data: employeeDetails } = useQuery({
    queryKey: ['kobetsu-employees', id],
    queryFn: () => kobetsuApi.getEmployeeDetails(id),
    enabled: !!id,
  })

  const activateMutation = useMutation({
    mutationFn: () => kobetsuApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu', id] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => kobetsuApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      router.push('/kobetsu')
    },
  })

  const handleGeneratePDF = async () => {
    try {
      const blob = await kobetsuApi.generatePDF(id, 'pdf')
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${contract?.contract_number}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert('PDF生成に失敗しました')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  if (error || !contract) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">契約書が見つかりません</p>
        <Link href="/kobetsu" className="btn-primary">
          一覧に戻る
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          dashboardBreadcrumb,
          { label: '個別契約書', href: '/kobetsu' },
          { label: contract.contract_number }
        ]}
        className="mb-4"
      />

      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              {contract.contract_number}
            </h1>
            <StatusBadge status={contract.status} />
          </div>
          <p className="text-gray-500 mt-1">
            {contract.worksite_name}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/kobetsu" className="btn-secondary">
            ← 一覧に戻る
          </Link>
          {contract.status === 'draft' && (
            <>
              <Link href={`/kobetsu/${id}/edit`} className="btn-secondary">
                編集
              </Link>
              <button
                onClick={() => activateMutation.mutate()}
                className="btn-primary"
                disabled={activateMutation.isPending}
              >
                有効化
              </button>
            </>
          )}
          <button onClick={handleGeneratePDF} className="btn-secondary">
            PDF出力
          </button>
        </div>
      </div>

      {/* Contract Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">基本情報</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">契約番号</p>
                <p className="font-medium">{contract.contract_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">契約締結日</p>
                <p className="font-medium">
                  {new Date(contract.contract_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣開始日</p>
                <p className="font-medium">
                  {new Date(contract.dispatch_start_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣終了日</p>
                <p className="font-medium">
                  {new Date(contract.dispatch_end_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣労働者数</p>
                <p className="font-medium">{contract.number_of_workers}名</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">ステータス</p>
                <StatusBadge status={contract.status} />
              </div>
            </div>
          </div>
        </div>

        {/* Work Location */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">就業場所</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">事業所名称</p>
              <p className="font-medium">{contract.worksite_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">所在地</p>
              <p className="font-medium">{contract.worksite_address}</p>
            </div>
            {contract.organizational_unit && (
              <div>
                <p className="text-sm text-gray-500">組織単位</p>
                <p className="font-medium">{contract.organizational_unit}</p>
              </div>
            )}
          </div>
        </div>

        {/* Work Content */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">業務内容</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">業務内容</p>
              <p className="font-medium whitespace-pre-wrap">{contract.work_content}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">責任の程度</p>
              <p className="font-medium">{contract.responsibility_level}</p>
            </div>
          </div>
        </div>

        {/* Supervisor */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">指揮命令者</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">部署</p>
                <p className="font-medium">{contract.supervisor_department}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">役職</p>
                <p className="font-medium">{contract.supervisor_position}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">氏名</p>
                <p className="font-medium">{contract.supervisor_name}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Working Hours */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">就業時間</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">就業日</p>
              <p className="font-medium">{contract.work_days?.join('、')}</p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">始業時刻</p>
                <p className="font-medium">{contract.work_start_time}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">終業時刻</p>
                <p className="font-medium">{contract.work_end_time}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">休憩時間</p>
                <p className="font-medium">{contract.break_time_minutes}分</p>
              </div>
            </div>
          </div>
        </div>

        {/* Rates */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">派遣料金</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">基本時間単価</p>
                <p className="font-medium text-lg">¥{Number(contract.hourly_rate).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">時間外単価</p>
                <p className="font-medium text-lg">¥{Number(contract.overtime_rate).toLocaleString()}</p>
              </div>
              {contract.night_shift_rate && (
                <div>
                  <p className="text-sm text-gray-500">深夜単価</p>
                  <p className="font-medium">¥{Number(contract.night_shift_rate).toLocaleString()}</p>
                </div>
              )}
              {contract.holiday_rate && (
                <div>
                  <p className="text-sm text-gray-500">休日単価</p>
                  <p className="font-medium">¥{Number(contract.holiday_rate).toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Employees Section */}
      <div className="card">
        <div className="card-header flex justify-between items-center">
          <h2 className="text-lg font-semibold">
            派遣労働者一覧
            {employeeDetails?.total_employees && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({employeeDetails.total_employees}名)
              </span>
            )}
          </h2>
          <Link
            href={`/assign?factory_id=${contract.factory_id}`}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            + 従業員を追加
          </Link>
        </div>
        <div className="card-body p-0">
          {employeeDetails?.employees?.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      社員番号
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      氏名
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      国籍
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      時給単価
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      単価ソース
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      雇用形態
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      期間
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {employeeDetails.employees.map((emp: any) => (
                    <tr key={emp.employee_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {emp.employee_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{emp.full_name_kanji}</div>
                          <div className="text-sm text-gray-500">{emp.full_name_kana}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {emp.nationality}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        <span className="font-medium text-gray-900">
                          ¥{emp.effective_rate?.toLocaleString() || '-'}
                        </span>
                        {emp.individual_rate && (
                          <span className="ml-1 text-xs text-blue-600">(個別)</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                          emp.rate_source === 'individual'
                            ? 'bg-blue-100 text-blue-800'
                            : emp.rate_source === 'employee'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {emp.rate_source === 'individual' ? '個別' :
                           emp.rate_source === 'employee' ? '従業員' : '契約'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                          emp.is_indefinite_employment
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {emp.employment_type_display}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {emp.individual_start_date || emp.individual_end_date ? (
                          <span>
                            {emp.individual_start_date && (
                              <span>{new Date(emp.individual_start_date).toLocaleDateString('ja-JP')}</span>
                            )}
                            {' ~ '}
                            {emp.individual_end_date && (
                              <span>{new Date(emp.individual_end_date).toLocaleDateString('ja-JP')}</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-gray-400">契約期間通り</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500">
              <p>従業員が登録されていません</p>
              <Link
                href={`/assign?factory_id=${contract.factory_id}`}
                className="mt-2 inline-block text-blue-600 hover:text-blue-700"
              >
                従業員を追加する
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      {contract.notes && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">備考</h2>
          </div>
          <div className="card-body">
            <p className="whitespace-pre-wrap">{contract.notes}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      {contract.status === 'draft' && (
        <div className="card border-red-200">
          <div className="card-body">
            <h3 className="text-lg font-semibold text-red-600 mb-4">危険な操作</h3>
            <button
              onClick={() => {
                if (confirm('この契約書を削除しますか？この操作は取り消せません。')) {
                  deleteMutation.mutate()
                }
              }}
              className="btn-danger"
              disabled={deleteMutation.isPending}
            >
              契約書を削除
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
