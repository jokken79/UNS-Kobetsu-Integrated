'use client'

import { useToast, useToastActions } from '@/components/common/ToastContext'

export default function ToastDemoPage() {
  const { showToast } = useToast()
  const toast = useToastActions()

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Toast Notification Demo</h1>

      <div className="space-y-4">
        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Basic Toast Types</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => toast.success('保存しました')}
              className="px-4 py-2 bg-emerald-500 text-white rounded hover:bg-emerald-600"
            >
              Success Toast
            </button>

            <button
              onClick={() => toast.error('エラーが発生しました')}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Error Toast
            </button>

            <button
              onClick={() => toast.warning('注意が必要です')}
              className="px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
            >
              Warning Toast
            </button>

            <button
              onClick={() => toast.info('お知らせがあります')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Info Toast
            </button>
          </div>
        </div>

        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Custom Duration</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => showToast({
                type: 'success',
                message: '3秒で消えます',
                duration: 3000
              })}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              3 Second Toast
            </button>

            <button
              onClick={() => showToast({
                type: 'error',
                message: 'このエラーは8秒間表示されます',
                duration: 8000
              })}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              8 Second Toast
            </button>

            <button
              onClick={() => showToast({
                type: 'info',
                message: '手動で閉じるまで表示されます',
                duration: 0
              })}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              No Auto-dismiss
            </button>
          </div>
        </div>

        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Multiple Toasts</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {
                toast.success('最初のメッセージ')
                setTimeout(() => toast.info('2番目のメッセージ'), 500)
                setTimeout(() => toast.warning('3番目のメッセージ'), 1000)
              }}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
            >
              Show 3 Toasts
            </button>

            <button
              onClick={() => {
                for (let i = 1; i <= 7; i++) {
                  setTimeout(() => {
                    showToast({
                      type: ['success', 'error', 'warning', 'info'][Math.floor(Math.random() * 4)] as any,
                      message: `Toast ${i}/7 (最大5個まで表示)`,
                      duration: 5000
                    })
                  }, i * 300)
                }
              }}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
            >
              Test Max 5 Toasts
            </button>
          </div>
        </div>

        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Real-world Examples</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {
                toast.success('契約書が正常に作成されました')
              }}
              className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
            >
              Contract Created
            </button>

            <button
              onClick={() => {
                toast.error('必須項目を入力してください: 派遣先、業務内容')
              }}
              className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
            >
              Validation Error
            </button>

            <button
              onClick={() => {
                toast.warning('契約期限が30日以内に満了します')
              }}
              className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
            >
              Expiry Warning
            </button>

            <button
              onClick={() => {
                toast.info('新しい従業員データが同期されました')
              }}
              className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
            >
              Sync Complete
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 p-4 bg-gray-100 rounded-lg">
        <h3 className="font-semibold mb-2">Usage Example:</h3>
        <pre className="text-sm bg-white p-3 rounded border">
{`import { useToast } from '@/components/common/ToastContext'

function MyComponent() {
  const { showToast } = useToast()

  const handleSave = async () => {
    try {
      await saveData()
      showToast({
        type: 'success',
        message: '保存しました'
      })
    } catch (error) {
      showToast({
        type: 'error',
        message: 'エラーが発生しました',
        duration: 8000
      })
    }
  }
}`}</pre>
      </div>
    </div>
  )
}