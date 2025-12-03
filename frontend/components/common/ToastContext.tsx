'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { ToastType } from './Toast'
import { ToastContainer } from './ToastContainer'

interface ToastData {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ShowToastOptions {
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextValue {
  showToast: (options: ShowToastOptions) => void
  clearToasts: () => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

let toastId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastData[]>([])

  const showToast = useCallback((options: ShowToastOptions) => {
    const id = `toast-${++toastId}`
    const newToast: ToastData = {
      id,
      type: options.type,
      message: options.message,
      duration: options.duration ?? 5000,
    }

    setToasts((prevToasts) => {
      // Limit to 5 toasts maximum
      const updatedToasts = [...prevToasts, newToast]
      if (updatedToasts.length > 5) {
        return updatedToasts.slice(-5)
      }
      return updatedToasts
    })
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    setToasts([])
  }, [])

  const contextValue: ToastContextValue = {
    showToast,
    clearToasts,
  }

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Convenience functions for common toast types
export function useToastActions() {
  const { showToast } = useToast()

  return {
    success: (message: string, duration?: number) =>
      showToast({ type: 'success', message, duration }),
    error: (message: string, duration?: number) =>
      showToast({ type: 'error', message, duration }),
    warning: (message: string, duration?: number) =>
      showToast({ type: 'warning', message, duration }),
    info: (message: string, duration?: number) =>
      showToast({ type: 'info', message, duration }),
  }
}