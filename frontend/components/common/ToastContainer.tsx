'use client'

import { Toast, ToastProps } from './Toast'

interface ToastContainerProps {
  toasts: Omit<ToastProps, 'onClose'>[]
  onClose: (id: string) => void
}

export function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div
      aria-live="assertive"
      className="pointer-events-none fixed inset-0 flex items-end px-4 py-6 sm:items-start sm:p-6 z-50"
    >
      <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto w-full max-w-sm">
            <Toast {...toast} onClose={onClose} />
          </div>
        ))}
      </div>
    </div>
  )
}