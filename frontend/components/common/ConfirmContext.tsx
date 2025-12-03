'use client'

import { createContext, useContext, useState, useCallback, ReactNode, useRef } from 'react'
import { ConfirmDialog, ConfirmType } from './ConfirmDialog'

interface ConfirmOptions {
  type?: ConfirmType
  title: string
  message: string
  confirmText?: string
  cancelText?: string
}

interface ConfirmContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ConfirmContext = createContext<ConfirmContextValue | undefined>(undefined)

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean
    type: ConfirmType
    title: string
    message: string
    confirmText?: string
    cancelText?: string
  }>({
    isOpen: false,
    type: 'info',
    title: '',
    message: '',
  })

  const resolveRef = useRef<((value: boolean) => void) | null>(null)

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      resolveRef.current = resolve

      setDialogState({
        isOpen: true,
        type: options.type || 'info',
        title: options.title,
        message: options.message,
        confirmText: options.confirmText,
        cancelText: options.cancelText,
      })
    })
  }, [])

  const handleConfirm = useCallback(() => {
    setDialogState((prev) => ({ ...prev, isOpen: false }))
    if (resolveRef.current) {
      resolveRef.current(true)
      resolveRef.current = null
    }
  }, [])

  const handleCancel = useCallback(() => {
    setDialogState((prev) => ({ ...prev, isOpen: false }))
    if (resolveRef.current) {
      resolveRef.current(false)
      resolveRef.current = null
    }
  }, [])

  const contextValue: ConfirmContextValue = {
    confirm,
  }

  return (
    <ConfirmContext.Provider value={contextValue}>
      {children}
      <ConfirmDialog
        isOpen={dialogState.isOpen}
        type={dialogState.type}
        title={dialogState.title}
        message={dialogState.message}
        confirmText={dialogState.confirmText}
        cancelText={dialogState.cancelText}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const context = useContext(ConfirmContext)
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider')
  }
  return context
}

// Convenience hooks for common confirm types
export function useConfirmActions() {
  const { confirm } = useConfirm()

  return {
    confirmDelete: (itemName?: string) =>
      confirm({
        type: 'danger',
        title: '削除の確認',
        message: itemName
          ? `${itemName}を削除しますか？この操作は取り消せません。`
          : 'このアイテムを削除しますか？この操作は取り消せません。',
        confirmText: '削除する',
        cancelText: 'キャンセル',
      }),

    confirmWarning: (title: string, message: string) =>
      confirm({
        type: 'warning',
        title,
        message,
        confirmText: '続行する',
        cancelText: 'キャンセル',
      }),

    confirmInfo: (title: string, message: string) =>
      confirm({
        type: 'info',
        title,
        message,
        confirmText: '確認',
        cancelText: 'キャンセル',
      }),

    confirmSave: (hasUnsavedChanges: boolean = true) =>
      confirm({
        type: 'warning',
        title: '未保存の変更',
        message: hasUnsavedChanges
          ? '未保存の変更があります。ページを離れてもよろしいですか？'
          : '変更を保存しますか？',
        confirmText: hasUnsavedChanges ? '離れる' : '保存する',
        cancelText: 'キャンセル',
      }),

    confirmLogout: () =>
      confirm({
        type: 'info',
        title: 'ログアウトの確認',
        message: 'ログアウトしてもよろしいですか？',
        confirmText: 'ログアウト',
        cancelText: 'キャンセル',
      }),
  }
}