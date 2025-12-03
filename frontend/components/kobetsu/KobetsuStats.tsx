'use client'

import type { KobetsuStats as StatsType } from '@/types'
import { SkeletonStats } from '@/components/common/Skeleton'

interface KobetsuStatsProps {
  stats?: StatsType
  isLoading?: boolean
}

// SVG Icons
const Icons = {
  Document: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Check: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Warning: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  ),
  Edit: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
    </svg>
  ),
  XCircle: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Users: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  TrendUp: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
    </svg>
  ),
}

export function KobetsuStats({ stats, isLoading }: KobetsuStatsProps) {
  const statCards = [
    {
      label: '総契約数',
      value: stats?.total_contracts ?? 0,
      icon: Icons.Document,
      gradient: 'from-blue-500 to-blue-600',
      shadowColor: 'shadow-blue-500/30',
      bgLight: 'bg-blue-50',
      textColor: 'text-blue-600',
    },
    {
      label: '有効な契約',
      value: stats?.active_contracts ?? 0,
      icon: Icons.Check,
      gradient: 'from-emerald-500 to-emerald-600',
      shadowColor: 'shadow-emerald-500/30',
      bgLight: 'bg-emerald-50',
      textColor: 'text-emerald-600',
    },
    {
      label: '期限間近',
      value: stats?.expiring_soon ?? 0,
      icon: Icons.Warning,
      gradient: 'from-amber-400 to-orange-500',
      shadowColor: 'shadow-amber-500/30',
      bgLight: 'bg-amber-50',
      textColor: 'text-amber-600',
      highlight: (stats?.expiring_soon ?? 0) > 0,
    },
    {
      label: '下書き',
      value: stats?.draft_contracts ?? 0,
      icon: Icons.Edit,
      gradient: 'from-slate-500 to-slate-600',
      shadowColor: 'shadow-slate-500/30',
      bgLight: 'bg-slate-50',
      textColor: 'text-slate-600',
    },
    {
      label: '期限切れ',
      value: stats?.expired_contracts ?? 0,
      icon: Icons.XCircle,
      gradient: 'from-rose-500 to-red-600',
      shadowColor: 'shadow-rose-500/30',
      bgLight: 'bg-rose-50',
      textColor: 'text-rose-600',
      highlight: (stats?.expired_contracts ?? 0) > 0,
    },
    {
      label: '派遣労働者数',
      value: stats?.total_workers ?? 0,
      icon: Icons.Users,
      gradient: 'from-violet-500 to-purple-600',
      shadowColor: 'shadow-violet-500/30',
      bgLight: 'bg-violet-50',
      textColor: 'text-violet-600',
    },
  ]

  if (isLoading) {
    return <SkeletonStats count={6} />
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon
        return (
          <div
            key={stat.label}
            className={`group relative bg-white rounded-xl border border-gray-200/60 p-5
                        shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1
                        ${stat.highlight ? 'ring-2 ring-amber-400 ring-offset-2' : ''}
                        animate-slide-up`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {/* Background decoration */}
            <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.gradient}
                            opacity-5 rounded-bl-[100px] transition-opacity group-hover:opacity-10`} />

            {/* Icon */}
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl
                            bg-gradient-to-br ${stat.gradient} text-white shadow-lg ${stat.shadowColor}
                            mb-4 transition-transform group-hover:scale-110`}>
              <Icon />
            </div>

            {/* Value */}
            <p className="text-3xl font-bold text-gray-900 tracking-tight">
              {stat.value.toLocaleString()}
            </p>

            {/* Label */}
            <p className="text-sm font-medium text-gray-500 mt-1">
              {stat.label}
            </p>

            {/* Trend indicator (optional) */}
            {stat.highlight && stat.value > 0 && (
              <div className="absolute top-3 right-3">
                <span className="flex h-3 w-3">
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full
                                   ${stat.label === '期限間近' ? 'bg-amber-400' : 'bg-rose-400'} opacity-75`} />
                  <span className={`relative inline-flex rounded-full h-3 w-3
                                   ${stat.label === '期限間近' ? 'bg-amber-500' : 'bg-rose-500'}`} />
                </span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
