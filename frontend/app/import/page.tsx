'use client'

import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { importApi, ImportResponse } from '@/lib/api'
import Link from 'next/link'

type ImportType = 'factories' | 'employees'
type ImportMode = 'create' | 'update' | 'sync'

interface TableStats {
  name: string
  displayName: string
  count: number
  icon: string
  color: string
  viewUrl?: string
  createUrl?: string
  canImport: boolean
  canExport: boolean
}

// API base URL for exports
const API_URL = '/api/v1'

export default function DataManagementPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'import' | 'export'>('overview')
  const [importType, setImportType] = useState<ImportType>('employees')
  const [importMode, setImportMode] = useState<ImportMode>('sync')
  const [isDragging, setIsDragging] = useState(false)
  const [previewData, setPreviewData] = useState<ImportResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [batchResults, setBatchResults] = useState<ImportResponse[]>([])
  const queryClient = useQueryClient()

  // Fetch table statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['table-stats'],
    queryFn: async () => {
      const [employeesRes, factoriesRes, kobetsuRes] = await Promise.all([
        fetch(`${API_URL}/employees/stats`).then(r => r.json()).catch(() => ({ total_employees: 0, active_employees: 0 })),
        fetch(`${API_URL}/factories/stats`).then(r => r.json()).catch(() => ({ total_factories: 0 })),
        fetch(`${API_URL}/kobetsu?limit=1`).then(r => r.json()).catch(() => ({ items: [] })),
      ])

      // Get counts from various endpoints
      const employeeCount = employeesRes.total_employees || 0
      const activeEmployees = employeesRes.active_employees || 0
      const factoryCount = factoriesRes.total_factories || 0

      return {
        employees: { total: employeeCount, active: activeEmployees },
        factories: { total: factoryCount },
        kobetsu: { total: kobetsuRes.items?.length || 0 }
      }
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  // Table definitions
  const tables: TableStats[] = [
    {
      name: 'employees',
      displayName: '従業員マスタ',
      count: stats?.employees?.total || 0,
      icon: '👥',
      color: 'bg-blue-500',
      viewUrl: '/employees',
      createUrl: '/employees/create',
      canImport: true,
      canExport: true
    },
    {
      name: 'factories',
      displayName: '工場マスタ (派遣先)',
      count: stats?.factories?.total || 0,
      icon: '🏭',
      color: 'bg-green-500',
      viewUrl: '/factories',
      createUrl: '/factories/create',
      canImport: true,
      canExport: true
    },
    {
      name: 'kobetsu',
      displayName: '個別契約書',
      count: stats?.kobetsu?.total || 0,
      icon: '📄',
      color: 'bg-purple-500',
      viewUrl: '/kobetsu',
      createUrl: '/kobetsu/create',
      canImport: false,
      canExport: true
    }
  ]

  // Import mutations
  const previewMutation = useMutation({
    mutationFn: async (file: File) => {
      if (importType === 'factories') {
        return importApi.previewFactories(file)
      } else {
        return importApi.previewEmployees(file)
      }
    },
    onSuccess: (data) => {
      setPreviewData(data)
    },
  })

  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!previewData) return
      if (importType === 'factories') {
        return importApi.executeFactoryImport(previewData.preview_data, importMode)
      } else {
        return importApi.executeEmployeeImport(previewData.preview_data, importMode)
      }
    },
    onSuccess: (data) => {
      if (data) {
        setPreviewData(data)
        queryClient.invalidateQueries({ queryKey: ['table-stats'] })
      }
    },
  })

  const syncMutation = useMutation({
    mutationFn: async (file: File) => {
      return importApi.syncEmployees(file)
    },
    onSuccess: (data) => {
      setPreviewData(data)
      queryClient.invalidateQueries({ queryKey: ['table-stats'] })
    },
  })

  // Handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [importType])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      // For factories with multiple JSON files
      if (importType === 'factories' && files.length > 1) {
        const fileArray = Array.from(files)
        setSelectedFiles(fileArray)
        setSelectedFile(null)
        setPreviewData(null)
        setBatchResults([])
      } else {
        // Single file (employees or single factory)
        handleFile(files[0])
      }
    }
  }

  const handleFile = (file: File) => {
    setSelectedFile(file)
    setSelectedFiles([])
    setPreviewData(null)
    setBatchResults([])
    previewMutation.mutate(file)
  }

  const handleExecute = () => {
    executeMutation.mutate()
  }

  const handleQuickSync = () => {
    if (selectedFile) {
      syncMutation.mutate(selectedFile)
    }
  }

  const handleBatchImport = async () => {
    if (selectedFiles.length === 0) return

    setBatchResults([])
    let successCount = 0
    let errorCount = 0

    for (const file of selectedFiles) {
      try {
        const result = await importApi.previewFactories(file)
        if (result.preview_data.length > 0) {
          const executed = await importApi.executeFactoryImport(result.preview_data, importMode)
          if (executed) {
            setBatchResults(prev => [...prev, executed])
            successCount++
          }
        }
      } catch (error) {
        console.error(`Error importing ${file.name}:`, error)
        errorCount++
      }
    }

    queryClient.invalidateQueries({ queryKey: ['table-stats'] })
    alert(`インポート完了!\n成功: ${successCount} ファイル\nエラー: ${errorCount} ファイル`)
  }

  const handleReset = () => {
    setPreviewData(null)
    setSelectedFile(null)
    setSelectedFiles([])
    setBatchResults([])
    previewMutation.reset()
    executeMutation.reset()
    syncMutation.reset()
  }

  const handleExport = async (tableName: string) => {
    try {
      let url = ''
      let filename = ''

      switch (tableName) {
        case 'employees':
          url = `${API_URL}/employees?limit=1500&status=`
          filename = 'employees_export.json'
          break
        case 'factories':
          url = `${API_URL}/factories?limit=500`
          filename = 'factories_export.json'
          break
        case 'kobetsu':
          url = `${API_URL}/kobetsu?limit=500`
          filename = 'kobetsu_export.json'
          break
        default:
          return
      }

      const response = await fetch(url)
      const data = await response.json()

      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(downloadUrl)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Export failed:', error)
      alert('エクスポートに失敗しました')
    }
  }

  const handleDeleteAll = async (tableName: string) => {
    // Confirmación doble para operaciones peligrosas
    const tableDisplayNames: Record<string, string> = {
      'employees': '従業員マスタ',
      'factories': '工場マスタ',
      'kobetsu': '個別契約書'
    }

    const displayName = tableDisplayNames[tableName] || tableName
    const confirmMessage = `⚠️ 警告: ${displayName}の全データを削除します。\n\nこの操作は取り消せません。本当に削除しますか？`

    if (!confirm(confirmMessage)) {
      return
    }

    const doubleConfirm = prompt(`確認のため「削除」と入力してください:`)
    if (doubleConfirm !== '削除') {
      alert('キャンセルされました')
      return
    }

    try {
      let url = ''

      switch (tableName) {
        case 'employees':
          url = `${API_URL}/employees/delete-all`
          break
        case 'factories':
          url = `${API_URL}/factories/delete-all`
          break
        case 'kobetsu':
          url = `${API_URL}/kobetsu/delete-all`
          break
        default:
          return
      }

      // Get auth token from localStorage
      const token = localStorage.getItem('access_token')

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `削除に失敗しました: ${response.statusText}`)
      }

      const result = await response.json()

      // Refresh stats
      queryClient.invalidateQueries({ queryKey: ['table-stats'] })

      alert(`✅ ${displayName}のデータを削除しました\n削除件数: ${result.deleted_count || 0}件`)
    } catch (error) {
      console.error('Delete all failed:', error)
      alert(`❌ 削除に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`)
    }
  }

  const isLoading = previewMutation.isPending || executeMutation.isPending || syncMutation.isPending

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">データ管理</h1>
      <p className="text-gray-600 mb-6">マスタデータの閲覧・インポート・エクスポート</p>

      {/* Tab Navigation */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-3 font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📊 データ概要
        </button>
        <button
          onClick={() => setActiveTab('import')}
          className={`px-6 py-3 font-medium border-b-2 transition-colors ${
            activeTab === 'import'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📥 インポート
        </button>
        <button
          onClick={() => setActiveTab('export')}
          className={`px-6 py-3 font-medium border-b-2 transition-colors ${
            activeTab === 'export'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📤 エクスポート
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {tables.map((table) => (
              <div key={table.name} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className={`${table.color} px-4 py-3 text-white`}>
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{table.icon}</span>
                    <span className="text-3xl font-bold">
                      {statsLoading ? '...' : table.count.toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-3">{table.displayName}</h3>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {table.viewUrl && (
                      <Link
                        href={table.viewUrl}
                        className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                      >
                        一覧表示
                      </Link>
                    )}
                    {table.createUrl && (
                      <Link
                        href={table.createUrl}
                        className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                      >
                        新規作成
                      </Link>
                    )}
                    {table.canImport && (
                      <button
                        onClick={() => {
                          setImportType(table.name as ImportType)
                          setActiveTab('import')
                        }}
                        className="px-3 py-1.5 bg-green-100 text-green-700 rounded hover:bg-green-200 text-sm"
                      >
                        インポート
                      </button>
                    )}
                    {table.canExport && (
                      <button
                        onClick={() => handleExport(table.name)}
                        className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 text-sm"
                      >
                        エクスポート
                      </button>
                    )}
                  </div>
                  {/* Delete All Button */}
                  <button
                    onClick={() => handleDeleteAll(table.name)}
                    className="w-full px-3 py-1.5 bg-red-50 text-red-700 rounded hover:bg-red-100 text-sm font-medium border border-red-200 flex items-center justify-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    全データ削除
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Stats */}
          {stats?.employees && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="font-semibold text-lg mb-4">従業員統計</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{stats.employees.total}</div>
                  <div className="text-sm text-gray-600">総従業員数</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{stats.employees.active}</div>
                  <div className="text-sm text-gray-600">在籍中</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">{stats.employees.total - stats.employees.active}</div>
                  <div className="text-sm text-gray-600">退社済み</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{stats.factories?.total || 0}</div>
                  <div className="text-sm text-gray-600">派遣先数</div>
                </div>
              </div>
            </div>
          )}

          {/* Database Admin Link */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold mb-2">データベース直接アクセス</h3>
            <p className="text-sm text-gray-600 mb-3">
              Adminerを使用してデータベースを直接操作できます（上級者向け）
            </p>
            <a
              href="http://localhost:8090"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
            >
              🗃️ Adminer を開く
            </a>
            <span className="ml-4 text-sm text-gray-500">
              Server: uns-kobetsu-db | User: kobetsu_admin | DB: kobetsu_db
            </span>
          </div>
        </div>
      )}

      {/* Import Tab */}
      {activeTab === 'import' && (
        <div>
          {/* Import Type Selection */}
          <div className="mb-6 flex gap-4">
            <button
              onClick={() => { setImportType('employees'); handleReset() }}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                importType === 'employees'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              👥 従業員マスタ
            </button>
            <button
              onClick={() => { setImportType('factories'); handleReset() }}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                importType === 'factories'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🏭 工場マスタ
            </button>
          </div>

          {/* Template Download */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">テンプレートをダウンロード:</p>
            <div className="flex gap-2">
              {importType === 'factories' ? (
                <>
                  <a
                    href={importApi.downloadFactoryTemplate('excel')}
                    className="text-blue-600 hover:underline text-sm"
                    download
                  >
                    Excel テンプレート
                  </a>
                  <span className="text-gray-400">|</span>
                  <a
                    href={importApi.downloadFactoryTemplate('json')}
                    className="text-blue-600 hover:underline text-sm"
                    download
                  >
                    JSON テンプレート
                  </a>
                </>
              ) : (
                <>
                  <a
                    href={importApi.downloadEmployeeTemplate()}
                    className="text-blue-600 hover:underline text-sm"
                    download
                  >
                    Excel テンプレート
                  </a>
                  <span className="text-gray-400 mx-2">|</span>
                  <span className="text-sm text-gray-500">
                    または 社員台帳.xlsm (DBGenzaiXシート) をそのままアップロード
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <p className="text-lg text-gray-600 mb-2">
              ファイルをドラッグ＆ドロップ
            </p>
            <p className="text-sm text-gray-500 mb-4">
              {importType === 'factories'
                ? 'JSON または Excel (.xlsx, .xlsm) - 複数ファイル選択可能 ✨'
                : 'Excel (.xlsx, .xlsm) - 社員台帳のDBGenzaiXシートを自動検出'}
            </p>
            <label className="inline-block">
              <span className="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700">
                ファイルを選択
              </span>
              <input
                type="file"
                className="hidden"
                accept={importType === 'factories' ? '.json,.xlsx,.xls,.xlsm' : '.xlsx,.xls,.xlsm'}
                multiple={importType === 'factories'}
                onChange={handleFileSelect}
              />
            </label>

            {selectedFile && (
              <p className="mt-4 text-sm text-gray-600">
                選択中: {selectedFile.name}
              </p>
            )}

            {selectedFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  選択中: {selectedFiles.length} ファイル
                </p>
                <div className="max-h-40 overflow-auto bg-gray-50 rounded p-3 text-xs">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="py-1 text-gray-600">
                      {idx + 1}. {file.name}
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleBatchImport}
                  className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  🚀 {selectedFiles.length}ファイルを一括インポート
                </button>
              </div>
            )}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-3 text-blue-600" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-blue-600">処理中...</span>
            </div>
          )}

          {/* Preview Results */}
          {previewData && !isLoading && (
            <div className="mt-6">
              {/* Summary */}
              <div className={`p-4 rounded-lg mb-4 ${
                previewData.success ? 'bg-green-50' : 'bg-yellow-50'
              }`}>
                <p className={`font-medium ${previewData.success ? 'text-green-800' : 'text-yellow-800'}`}>
                  {previewData.message}
                </p>
                <div className="mt-2 text-sm text-gray-600 grid grid-cols-4 gap-4">
                  <div>
                    <span className="font-medium">合計:</span> {previewData.total_rows}件
                  </div>
                  {previewData.imported_count > 0 && (
                    <div>
                      <span className="font-medium text-green-600">新規:</span> {previewData.imported_count}件
                    </div>
                  )}
                  {previewData.updated_count > 0 && (
                    <div>
                      <span className="font-medium text-blue-600">更新:</span> {previewData.updated_count}件
                    </div>
                  )}
                  {previewData.skipped_count > 0 && (
                    <div>
                      <span className="font-medium text-gray-600">スキップ:</span> {previewData.skipped_count}件
                    </div>
                  )}
                </div>
              </div>

              {/* Errors */}
              {previewData.errors.length > 0 && (
                <div className="mb-4 p-4 bg-red-50 rounded-lg">
                  <p className="font-medium text-red-800 mb-2">
                    エラー ({previewData.errors.length}件)
                  </p>
                  <ul className="text-sm text-red-700 max-h-40 overflow-auto">
                    {previewData.errors.slice(0, 20).map((error, idx) => (
                      <li key={idx} className="mb-1">
                        行 {error.row}: {error.message}
                        {error.value && <span className="text-red-500"> (値: {error.value})</span>}
                      </li>
                    ))}
                    {previewData.errors.length > 20 && (
                      <li className="text-gray-500">... 他 {previewData.errors.length - 20} 件のエラー</li>
                    )}
                  </ul>
                </div>
              )}

              {/* Preview Table */}
              {previewData.preview_data.length > 0 && (
                <div className="bg-white rounded-lg border overflow-hidden">
                  <div className="p-4 border-b bg-gray-50">
                    <h3 className="font-medium">プレビュー (最大100件)</h3>
                  </div>
                  <div className="overflow-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left">行</th>
                          <th className="px-4 py-2 text-left">状態</th>
                          {importType === 'factories' ? (
                            <>
                              <th className="px-4 py-2 text-left">派遣先名</th>
                              <th className="px-4 py-2 text-left">工場名</th>
                              <th className="px-4 py-2 text-left">抵触日</th>
                            </>
                          ) : (
                            <>
                              <th className="px-4 py-2 text-left">社員№</th>
                              <th className="px-4 py-2 text-left">氏名</th>
                              <th className="px-4 py-2 text-left">カナ</th>
                              <th className="px-4 py-2 text-left">派遣先</th>
                              <th className="px-4 py-2 text-left">時給</th>
                            </>
                          )}
                          <th className="px-4 py-2 text-left">エラー</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.preview_data.slice(0, 100).map((item, idx) => (
                          <tr key={idx} className={`border-b ${!item.is_valid ? 'bg-red-50' : ''}`}>
                            <td className="px-4 py-2">{item.row}</td>
                            <td className="px-4 py-2">
                              {item.is_valid ? (
                                <span className="text-green-600">OK</span>
                              ) : (
                                <span className="text-red-600">NG</span>
                              )}
                            </td>
                            {importType === 'factories' ? (
                              <>
                                <td className="px-4 py-2">{String(item.company_name || '')}</td>
                                <td className="px-4 py-2">{String(item.plant_name || '')}</td>
                                <td className="px-4 py-2">{String(item.conflict_date || '')}</td>
                              </>
                            ) : (
                              <>
                                <td className="px-4 py-2">{String(item.employee_number || '')}</td>
                                <td className="px-4 py-2">{String(item.full_name_kanji || '')}</td>
                                <td className="px-4 py-2">{String(item.full_name_kana || '')}</td>
                                <td className="px-4 py-2">{String(item.company_name || '')}</td>
                                <td className="px-4 py-2">{item.hourly_rate ? `¥${item.hourly_rate}` : ''}</td>
                              </>
                            )}
                            <td className="px-4 py-2 text-red-600 text-xs">
                              {item.errors?.join(', ')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {previewData.preview_data.length > 0 && !executeMutation.isSuccess && (
                <div className="mt-6 flex gap-4">
                  {/* Import Mode Selection */}
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">モード:</label>
                    <select
                      value={importMode}
                      onChange={(e) => setImportMode(e.target.value as ImportMode)}
                      className="border rounded px-3 py-2 text-sm"
                    >
                      <option value="create">新規のみ作成</option>
                      <option value="update">既存のみ更新</option>
                      <option value="sync">同期 (新規+更新)</option>
                    </select>
                  </div>

                  <button
                    onClick={handleExecute}
                    disabled={isLoading}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    インポート実行
                  </button>

                  {importType === 'employees' && (
                    <button
                      onClick={handleQuickSync}
                      disabled={isLoading}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      クイック同期
                    </button>
                  )}

                  <button
                    onClick={handleReset}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  >
                    リセット
                  </button>
                </div>
              )}

              {/* Success Message */}
              {executeMutation.isSuccess && (
                <div className="mt-6 p-4 bg-green-100 rounded-lg">
                  <p className="text-green-800 font-medium">インポートが完了しました</p>
                  <button
                    onClick={handleReset}
                    className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    新しいインポートを開始
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tables.filter(t => t.canExport).map((table) => (
              <div key={table.name} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <span className="text-3xl mr-3">{table.icon}</span>
                  <div>
                    <h3 className="font-semibold text-lg">{table.displayName}</h3>
                    <p className="text-sm text-gray-500">{table.count.toLocaleString()} 件</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExport(table.name)}
                    className="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                  >
                    📥 JSON エクスポート
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold mb-2">エクスポート形式について</h3>
            <ul className="text-sm text-gray-600 list-disc list-inside">
              <li>JSON形式でダウンロードされます</li>
              <li>全件出力（最大10,000件）</li>
              <li>Excelで開く場合は、データ → JSONから取得 を使用してください</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
