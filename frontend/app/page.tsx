'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { kobetsuApi } from '@/lib/api'
import { KobetsuStats } from '@/components/kobetsu/KobetsuStats'
import { KobetsuTable } from '@/components/kobetsu/KobetsuTable'
import { SkeletonListItem } from '@/components/common/Skeleton'
import {
  ContractsByMonthChart,
  ContractsByStatusChart,
  EmployeesByFactoryChart,
} from '@/components/dashboard'

// SVG Icons
const Icons = {
  Plus: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  ),
  ArrowRight: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
    </svg>
  ),
  Warning: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  ),
  Calendar: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5m-9-6h.008v.008H12v-.008zM12 15h.008v.008H12V15zm0 2.25h.008v.008H12v-.008zM9.75 15h.008v.008H9.75V15zm0 2.25h.008v.008H9.75v-.008zM7.5 15h.008v.008H7.5V15zm0 2.25h.008v.008H7.5v-.008zm6.75-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V15zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H16.5v-.008zm0 2.25h.008v.008H16.5V15z" />
    </svg>
  ),
  Users: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  Document: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Edit: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
    </svg>
  ),
  Check: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Clock: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  ChartBar: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ),
}

export default function HomePage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['kobetsu-stats'],
    queryFn: () => kobetsuApi.getStats(),
  })

  const { data: recentContracts, isLoading: contractsLoading } = useQuery({
    queryKey: ['kobetsu-recent'],
    queryFn: () => kobetsuApi.getList({ limit: 5, sort_by: 'created_at', sort_order: 'desc' }),
  })

  const { data: expiringContracts } = useQuery({
    queryKey: ['kobetsu-expiring'],
    queryFn: () => kobetsuApi.getExpiring(30),
  })

  // Conflict date alerts
  const { data: conflictAlerts } = useQuery({
    queryKey: ['conflict-alerts'],
    queryFn: () => kobetsuApi.getConflictDateAlerts(90),
  })

  // Expiring contracts alerts
  const { data: expiringAlerts } = useQuery({
    queryKey: ['expiring-alerts'],
    queryFn: () => kobetsuApi.getExpiringContractsAlerts(30),
  })

  const quickActions = [
    {
      name: '従業員配属',
      description: '派遣労働者を契約に配属',
      href: '/assign',
      icon: Icons.Users,
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/25',
    },
    {
      name: '新規契約作成',
      description: '個別契約書を作成',
      href: '/kobetsu/create',
      icon: Icons.Document,
      gradient: 'from-emerald-500 to-emerald-600',
      shadow: 'shadow-emerald-500/25',
    },
    {
      name: '下書き一覧',
      description: '未完了の契約書',
      href: '/kobetsu?status=draft',
      icon: Icons.Edit,
      gradient: 'from-amber-400 to-orange-500',
      shadow: 'shadow-amber-500/25',
    },
    {
      name: '有効な契約',
      description: 'アクティブな契約',
      href: '/kobetsu?status=active',
      icon: Icons.Check,
      gradient: 'from-violet-500 to-purple-600',
      shadow: 'shadow-violet-500/25',
    },
    {
      name: '期限切れ',
      description: '満了した契約',
      href: '/kobetsu?status=expired',
      icon: Icons.ChartBar,
      gradient: 'from-slate-500 to-slate-600',
      shadow: 'shadow-slate-500/25',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
            ダッシュボード
          </h1>
          <p className="text-gray-500 mt-1">
            個別契約書の概要と最新情報
          </p>
        </div>
        <Link
          href="/kobetsu/create"
          className="btn-primary inline-flex items-center gap-2 self-start sm:self-auto"
        >
          <Icons.Plus />
          新規契約書作成
        </Link>
      </div>

      {/* Statistics Cards */}
      <KobetsuStats stats={stats} isLoading={statsLoading} />

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contracts by Month Chart */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600">
                <Icons.ChartBar />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  月別契約書作成数
                </h2>
                <p className="text-sm text-gray-500">過去6ヶ月の推移</p>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="h-64">
              <ContractsByMonthChart className="h-full" />
            </div>
          </div>
        </div>

        {/* Contracts by Status Chart */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600">
                <Icons.ChartBar />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  契約書ステータス
                </h2>
                <p className="text-sm text-gray-500">現在の状況</p>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="h-64">
              <ContractsByStatusChart className="h-full" />
            </div>
          </div>
        </div>

        {/* Employees by Factory Chart */}
        <div className="card lg:col-span-2">
          <div className="card-header">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
                <Icons.Users />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  派遣先別従業員数 (上位5社)
                </h2>
                <p className="text-sm text-gray-500">現在配属中の従業員</p>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="h-64">
              <EmployeesByFactoryChart className="h-full" />
            </div>
          </div>
        </div>
      </div>

      {/* Alert Banners */}
      {(conflictAlerts?.length > 0 || expiringAlerts?.length > 0) && (
        <div className="space-y-3">
          {/* Conflict Date Warning */}
          {conflictAlerts?.filter((a: any) => a.days_remaining <= 30).map((alert: any) => (
            <div
              key={alert.factory_id}
              className="alert-error animate-slide-up"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
                <Icons.Warning />
              </div>
              <div className="alert-content">
                <h4 className="alert-title">
                  抵触日警告: {alert.company_name} {alert.plant_name}
                </h4>
                <p className="alert-description">
                  抵触日まで残り <strong>{alert.days_remaining}日</strong>
                  （{alert.conflict_date}）- {alert.total_employees}名が影響を受けます
                </p>
              </div>
              <Link
                href={`/kobetsu?factory_id=${alert.factory_id}`}
                className="btn btn-sm bg-red-600 text-white hover:bg-red-700 flex-shrink-0"
              >
                確認
              </Link>
            </div>
          ))}

          {/* Expiring Contract Warning */}
          {expiringAlerts?.filter((a: any) => a.days_remaining <= 7).map((alert: any) => (
            <div
              key={alert.id}
              className="alert-warning animate-slide-up"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600">
                <Icons.Calendar />
              </div>
              <div className="alert-content">
                <h4 className="alert-title">
                  契約期限間近: {alert.contract_number}
                </h4>
                <p className="alert-description">
                  {alert.worksite_name} - 残り <strong>{alert.days_remaining}日</strong>
                  （{alert.dispatch_end_date}）- {alert.employee_count}名
                </p>
              </div>
              <Link
                href={`/kobetsu/${alert.id}`}
                className="btn btn-sm bg-amber-500 text-white hover:bg-amber-600 flex-shrink-0"
              >
                詳細
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Contracts */}
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600">
                <Icons.Clock />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  最近の契約書
                </h2>
                <p className="text-sm text-gray-500">最新の更新</p>
              </div>
            </div>
            <Link
              href="/kobetsu"
              className="btn btn-sm btn-ghost group"
            >
              すべて表示
              <span className="group-hover:translate-x-1 transition-transform">
                <Icons.ArrowRight />
              </span>
            </Link>
          </div>
          <div className="p-0">
            {contractsLoading ? (
              <div className="p-6 space-y-3">
                {[...Array(3)].map((_, i) => (
                  <SkeletonListItem key={i} />
                ))}
              </div>
            ) : recentContracts?.items?.length ? (
              <KobetsuTable contracts={recentContracts.items} compact />
            ) : (
              <div className="empty-state py-12">
                <div className="empty-state-icon">
                  <Icons.Document />
                </div>
                <p className="empty-state-title">契約書がありません</p>
                <p className="empty-state-description">
                  新しい契約書を作成して始めましょう
                </p>
                <Link href="/kobetsu/create" className="btn-primary">
                  契約書を作成
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Expiring Soon */}
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600">
                <Icons.Warning />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  期限間近の契約書
                </h2>
                <p className="text-sm text-gray-500">30日以内に満了</p>
              </div>
            </div>
            {expiringContracts?.length > 0 && (
              <span className="badge badge-expired">
                <span className="badge-dot" />
                {expiringContracts.length}件
              </span>
            )}
          </div>
          <div className="card-body">
            {expiringContracts?.length ? (
              <ul className="divide-y divide-gray-100">
                {expiringContracts.map((contract: any) => {
                  const daysLeft = Math.ceil(
                    (new Date(contract.dispatch_end_date).getTime() - new Date().getTime()) /
                    (1000 * 60 * 60 * 24)
                  )
                  return (
                    <li key={contract.id}>
                      <Link
                        href={`/kobetsu/${contract.id}`}
                        className="flex items-center justify-between py-3 -mx-2 px-2 rounded-lg
                                   hover:bg-gray-50 transition-colors group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold
                                          ${daysLeft <= 7
                                            ? 'bg-red-100 text-red-600'
                                            : 'bg-amber-100 text-amber-600'
                                          }`}>
                            {daysLeft}日
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                              {contract.contract_number}
                            </p>
                            <p className="text-sm text-gray-500 truncate">
                              {contract.worksite_name}
                            </p>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0 ml-4">
                          <p className={`text-sm font-medium ${daysLeft <= 7 ? 'text-red-600' : 'text-amber-600'}`}>
                            {new Date(contract.dispatch_end_date).toLocaleDateString('ja-JP')}
                          </p>
                          <p className="text-xs text-gray-400">
                            まで
                          </p>
                        </div>
                      </Link>
                    </li>
                  )
                })}
              </ul>
            ) : (
              <div className="empty-state py-8">
                <div className="empty-state-icon bg-emerald-100">
                  <span className="text-emerald-600"><Icons.Check /></span>
                </div>
                <p className="empty-state-title text-emerald-700">すべて順調!</p>
                <p className="empty-state-description">
                  期限間近の契約書はありません
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">
            クイックアクション
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">
            よく使う機能へのショートカット
          </p>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Link
                  key={action.name}
                  href={action.href}
                  className="group relative p-5 rounded-xl border border-gray-200
                             hover:border-gray-300 hover:shadow-lg
                             transition-all duration-300 hover:-translate-y-1"
                >
                  {/* Icon */}
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.gradient}
                                  flex items-center justify-center text-white shadow-lg ${action.shadow}
                                  mb-4 transition-transform group-hover:scale-110`}>
                    <Icon />
                  </div>

                  {/* Text */}
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                    {action.name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-1">
                    {action.description}
                  </p>

                  {/* Hover arrow */}
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400">
                    <Icons.ArrowRight />
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
