'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { kobetsuApi } from '@/lib/api'

// Lazy load heavy components
const KobetsuTable = dynamic(() => import('@/components/kobetsu/KobetsuTable').then(mod => mod.KobetsuTable), {
  loading: () => (
    <div className="p-12 text-center">
      <div className="spinner w-8 h-8 mx-auto mb-4"></div>
      <p className="text-gray-500">テーブルを読み込み中...</p>
    </div>
  ),
})

const KobetsuStats = dynamic(() => import('@/components/kobetsu/KobetsuStats').then(mod => mod.KobetsuStats), {
  loading: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 animate-pulse">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="bg-gray-100 rounded-lg h-24"></div>
      ))}
    </div>
  ),
})

export default function KobetsuListPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get query params
  const currentPage = Number(searchParams.get('page')) || 1
  const currentStatus = searchParams.get('status') || ''
  const currentSearch = searchParams.get('search') || ''

  const [search, setSearch] = useState(currentSearch)
  const [status, setStatus] = useState(currentStatus)
  const limit = 20

  // Fetch contracts
  const { data, isLoading, error } = useQuery({
    queryKey: ['kobetsu-list', currentPage, currentStatus, currentSearch],
    queryFn: () => kobetsuApi.getList({
      skip: (currentPage - 1) * limit,
      limit,
      status: currentStatus || undefined,
      search: currentSearch || undefined,
    }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['kobetsu-stats'],
    queryFn: () => kobetsuApi.getStats(),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (status) params.set('status', status)
    params.set('page', '1')
    router.push(`/kobetsu?${params.toString()}`)
  }

  const handleStatusFilter = (newStatus: string) => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (newStatus) params.set('status', newStatus)
    params.set('page', '1')
    setStatus(newStatus)
    router.push(`/kobetsu?${params.toString()}`)
  }

  const handlePageChange = (page: number) => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (status) params.set('status', status)
    params.set('page', page.toString())
    router.push(`/kobetsu?${params.toString()}`)
  }

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            個別契約書一覧
          </h1>
          <p className="text-gray-500 mt-1">
            すべての個別契約書を管理
          </p>
        </div>
        <Link href="/kobetsu/create" className="btn-primary">
          + 新規契約書作成
        </Link>
      </div>

      {/* Stats */}
      <KobetsuStats stats={stats} isLoading={!stats} />

      {/* Filters */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="契約番号または派遣先名で検索..."
                  className="form-input flex-1"
                />
                <button type="submit" className="btn-primary">
                  検索
                </button>
              </div>
            </form>

            {/* Status Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => handleStatusFilter('')}
                className={`btn ${!status ? 'btn-primary' : 'btn-secondary'}`}
              >
                すべて
              </button>
              <button
                onClick={() => handleStatusFilter('draft')}
                className={`btn ${status === 'draft' ? 'bg-amber-500 text-white' : 'btn-secondary'}`}
              >
                下書き
              </button>
              <button
                onClick={() => handleStatusFilter('active')}
                className={`btn ${status === 'active' ? 'bg-green-500 text-white' : 'btn-secondary'}`}
              >
                有効
              </button>
              <button
                onClick={() => handleStatusFilter('expired')}
                className={`btn ${status === 'expired' ? 'bg-red-500 text-white' : 'btn-secondary'}`}
              >
                期限切れ
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="card">
        <div className="card-body p-0">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="spinner w-8 h-8 mx-auto mb-4"></div>
              <p className="text-gray-500">読み込み中...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-red-600">
              エラーが発生しました。再度お試しください。
            </div>
          ) : data?.items?.length ? (
            <>
              <KobetsuTable contracts={data.items} />

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    全 {data.total} 件中 {(currentPage - 1) * limit + 1} - {Math.min(currentPage * limit, data.total)} 件を表示
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1}
                      className="btn-secondary disabled:opacity-50"
                    >
                      前へ
                    </button>
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let page = i + 1
                      if (totalPages > 5) {
                        if (currentPage > 3) {
                          page = currentPage - 2 + i
                        }
                        if (currentPage > totalPages - 2) {
                          page = totalPages - 4 + i
                        }
                      }
                      return (
                        <button
                          key={page}
                          onClick={() => handlePageChange(page)}
                          className={`btn ${currentPage === page ? 'btn-primary' : 'btn-secondary'}`}
                        >
                          {page}
                        </button>
                      )
                    })}
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= totalPages}
                      className="btn-secondary disabled:opacity-50"
                    >
                      次へ
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-500 mb-4">契約書が見つかりません</p>
              <Link href="/kobetsu/create" className="btn-primary">
                新規契約書を作成
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
