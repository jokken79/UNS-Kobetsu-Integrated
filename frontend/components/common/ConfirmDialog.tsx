'use client'

import { useEffect, useRef } from 'react'
import {
  TrashIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

export type ConfirmType = 'danger' | 'warning' | 'info'

export interface ConfirmDialogProps {
  isOpen: boolean
  type: ConfirmType
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
}

const dialogConfig = {
  danger: {
    icon: TrashIcon,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    confirmBg: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    confirmBg: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500',
  },
  info: {
    icon: InformationCircleIcon,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    confirmBg: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  },
}

export function ConfirmDialog({
  isOpen,
  type,
  title,
  message,
  confirmText = '確認',
  cancelText = 'キャンセル',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const config = dialogConfig[type]
  const Icon = config.icon

  // Focus trap and keyboard support
  useEffect(() => {
    if (!isOpen) return

    // Focus confirm button when dialog opens
    setTimeout(() => {
      confirmButtonRef.current?.focus()
    }, 50)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      } else if (e.key === 'Enter' && e.ctrlKey) {
        onConfirm()
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    // Prevent body scroll when dialog is open
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [isOpen, onConfirm, onCancel])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-gray-500 bg-opacity-75 backdrop-blur-sm transition-opacity z-40"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-md animate-fade-in-up"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className={`mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${config.iconBg} sm:mx-0 sm:h-10 sm:w-10`}>
                <Icon className={`h-6 w-6 ${config.iconColor}`} aria-hidden="true" />
              </div>
              <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                <h3 className="text-base font-semibold leading-6 text-gray-900">
                  {title}
                </h3>
                <div className="mt-2">
                  <p className="text-sm text-gray-600">
                    {message}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
            <button
              ref={confirmButtonRef}
              type="button"
              className={`inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm ${config.confirmBg} sm:ml-3 sm:w-auto focus:outline-none focus:ring-2 focus:ring-offset-2`}
              onClick={onConfirm}
            >
              {confirmText}
            </button>
            <button
              type="button"
              className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              onClick={onCancel}
            >
              {cancelText}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// Add custom animation to global styles if not exists
const style = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translate3d(0, 10%, 0);
    }
    to {
      opacity: 1;
      transform: translate3d(0, 0, 0);
    }
  }

  .animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out;
  }
`

if (typeof document !== 'undefined' && !document.getElementById('confirm-dialog-animations')) {
  const styleElement = document.createElement('style')
  styleElement.id = 'confirm-dialog-animations'
  styleElement.innerHTML = style
  document.head.appendChild(styleElement)
}