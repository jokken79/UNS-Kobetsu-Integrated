'use client'

import { useEffect, useState } from 'react'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/solid'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastProps {
  id: string
  type: ToastType
  message: string
  duration?: number
  onClose: (id: string) => void
}

const toastConfig = {
  success: {
    icon: CheckCircleIcon,
    bgColor: 'bg-emerald-500',
    textColor: 'text-emerald-500',
    borderColor: 'border-emerald-200',
    progressColor: 'bg-emerald-600',
  },
  error: {
    icon: XCircleIcon,
    bgColor: 'bg-red-500',
    textColor: 'text-red-500',
    borderColor: 'border-red-200',
    progressColor: 'bg-red-600',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bgColor: 'bg-amber-500',
    textColor: 'text-amber-500',
    borderColor: 'border-amber-200',
    progressColor: 'bg-amber-600',
  },
  info: {
    icon: InformationCircleIcon,
    bgColor: 'bg-blue-500',
    textColor: 'text-blue-500',
    borderColor: 'border-blue-200',
    progressColor: 'bg-blue-600',
  },
}

export function Toast({ id, type, message, duration = 5000, onClose }: ToastProps) {
  const [progress, setProgress] = useState(100)
  const [isExiting, setIsExiting] = useState(false)
  const config = toastConfig[type]
  const Icon = config.icon

  useEffect(() => {
    if (duration <= 0) return

    const startTime = Date.now()
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100)
      setProgress(remaining)

      if (remaining === 0) {
        clearInterval(interval)
        handleClose()
      }
    }, 50)

    return () => clearInterval(interval)
  }, [duration, id])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => onClose(id), 300) // Wait for animation to complete
  }

  return (
    <div
      className={`
        relative overflow-hidden bg-white rounded-lg shadow-lg border-l-4 ${config.borderColor}
        transform transition-all duration-300 ease-out
        ${isExiting ? 'translate-x-96 opacity-0' : 'translate-x-0 opacity-100'}
        animate-slide-in-right
      `}
      style={{
        animation: isExiting ? undefined : 'slideInRight 0.3s ease-out',
      }}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <Icon className={`h-6 w-6 ${config.textColor}`} aria-hidden="true" />
          </div>
          <div className="ml-3 w-0 flex-1">
            <p className="text-sm font-medium text-gray-900">
              {message}
            </p>
          </div>
          <div className="ml-4 flex flex-shrink-0">
            <button
              type="button"
              className="inline-flex rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              onClick={handleClose}
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
          <div
            className={`h-full ${config.progressColor} transition-all duration-100 ease-linear`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  )
}

// Add custom animation to global styles if not exists
const style = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`

if (typeof document !== 'undefined' && !document.getElementById('toast-animations')) {
  const styleElement = document.createElement('style')
  styleElement.id = 'toast-animations'
  styleElement.innerHTML = style
  document.head.appendChild(styleElement)
}