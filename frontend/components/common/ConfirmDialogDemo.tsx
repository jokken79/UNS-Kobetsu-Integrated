'use client'

import { useConfirm, useConfirmActions } from './ConfirmContext'
import { useToastActions } from './ToastContext'

export function ConfirmDialogDemo() {
  const { confirm } = useConfirm()
  const { confirmDelete, confirmWarning, confirmInfo, confirmSave, confirmLogout } = useConfirmActions()
  const toast = useToastActions()

  const handleBasicConfirm = async () => {
    const confirmed = await confirm({
      type: 'info',
      title: '確認',
      message: 'この操作を続行しますか？',
      confirmText: '続行',
      cancelText: 'キャンセル'
    })

    if (confirmed) {
      toast.success('操作を続行しました')
    } else {
      toast.info('操作をキャンセルしました')
    }
  }

  const handleDeleteFactory = async () => {
    const confirmed = await confirmDelete('高雄工業')

    if (confirmed) {
      toast.success('工場を削除しました')
    } else {
      toast.info('削除をキャンセルしました')
    }
  }

  const handleWarning = async () => {
    const confirmed = await confirmWarning(
      'データの不整合',
      '契約期間が重複しています。このまま保存しますか？'
    )

    if (confirmed) {
      toast.warning('重複を含む契約を保存しました')
    } else {
      toast.info('保存をキャンセルしました')
    }
  }

  const handleInfo = async () => {
    const confirmed = await confirmInfo(
      'バックアップの作成',
      'システムのバックアップを作成します。数分かかる場合があります。'
    )

    if (confirmed) {
      toast.info('バックアップを開始しました')
    } else {
      toast.info('バックアップをキャンセルしました')
    }
  }

  const handleUnsavedChanges = async () => {
    const confirmed = await confirmSave(true)

    if (confirmed) {
      toast.warning('未保存の変更を破棄しました')
    } else {
      toast.info('ページに留まります')
    }
  }

  const handleLogout = async () => {
    const confirmed = await confirmLogout()

    if (confirmed) {
      toast.success('ログアウトしました')
    } else {
      toast.info('ログアウトをキャンセルしました')
    }
  }

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold mb-4">Confirmation Dialog Examples</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <button
          onClick={handleBasicConfirm}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Basic Confirm
        </button>

        <button
          onClick={handleDeleteFactory}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          Delete Factory
        </button>

        <button
          onClick={handleWarning}
          className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          Warning Dialog
        </button>

        <button
          onClick={handleInfo}
          className="px-4 py-2 bg-sky-600 text-white rounded-md hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          Info Dialog
        </button>

        <button
          onClick={handleUnsavedChanges}
          className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          Unsaved Changes
        </button>

        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Logout Confirm
        </button>
      </div>
    </div>
  )
}