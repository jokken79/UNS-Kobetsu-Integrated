'use client'

import {
  Chart as ChartJS,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js'
import { Doughnut } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(ArcElement, Title, Tooltip, Legend)

interface ContractsByStatusChartProps {
  className?: string
}

export function ContractsByStatusChart({ className = '' }: ContractsByStatusChartProps) {
  // Mock data - in production, this would come from API
  const statusData = {
    draft: 8,
    active: 42,
    expired: 15,
    cancelled: 3,
    renewed: 12,
  }

  const data = {
    labels: ['下書き', '有効', '期限切れ', 'キャンセル', '更新済み'],
    datasets: [
      {
        data: [
          statusData.draft,
          statusData.active,
          statusData.expired,
          statusData.cancelled,
          statusData.renewed,
        ],
        backgroundColor: [
          'rgb(245, 158, 11)',  // amber-500 for draft
          'rgb(16, 185, 129)',  // emerald-500 for active
          'rgb(239, 68, 68)',   // red-500 for expired
          'rgb(107, 114, 128)',  // gray-500 for cancelled
          'rgb(139, 92, 246)',  // violet-500 for renewed
        ],
        borderColor: [
          'rgba(245, 158, 11, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(107, 114, 128, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderWidth: 0,
        hoverOffset: 8,
      },
    ],
  }

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          font: {
            size: 12,
          },
          color: '#4b5563',
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        titleFont: {
          size: 12,
        },
        bodyFont: {
          size: 14,
          weight: 'bold',
        },
        callbacks: {
          label: (context) => {
            const label = context.label || ''
            const value = context.parsed
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
            const percentage = ((value / total) * 100).toFixed(1)
            return `${label}: ${value}件 (${percentage}%)`
          },
        },
      },
    },
    cutout: '60%',
  }

  // Calculate total contracts
  const total = Object.values(statusData).reduce((sum, val) => sum + val, 0)

  return (
    <div className={`relative ${className}`}>
      <Doughnut data={data} options={options} />
      {/* Center total display */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900">{total}</div>
          <div className="text-sm text-gray-500">合計</div>
        </div>
      </div>
    </div>
  )
}