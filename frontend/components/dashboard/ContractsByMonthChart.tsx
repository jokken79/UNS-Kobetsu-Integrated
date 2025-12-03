'use client'

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface ContractsByMonthChartProps {
  className?: string
}

export function ContractsByMonthChart({ className = '' }: ContractsByMonthChartProps) {
  // Generate mock data for last 6 months
  const generateMonthLabels = () => {
    const months = []
    const now = new Date()

    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      months.push(`${year}-${month}`)
    }

    return months
  }

  // Mock data - in production, this would come from API
  const mockData = [12, 19, 15, 25, 22, 30]

  const data = {
    labels: generateMonthLabels(),
    datasets: [
      {
        label: '契約書作成数',
        data: mockData,
        backgroundColor: 'rgb(59, 130, 246)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 0,
        borderRadius: 6,
        barPercentage: 0.6,
      },
    ],
  }

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
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
            return `${context.parsed.y} 件`
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 12,
          },
          color: '#6b7280',
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(229, 231, 235, 0.5)',
          drawBorder: false,
        },
        ticks: {
          font: {
            size: 12,
          },
          color: '#6b7280',
          stepSize: 10,
          callback: function(value) {
            return value + '件'
          },
        },
      },
    },
  }

  return (
    <div className={`${className}`}>
      <Bar data={data} options={options} />
    </div>
  )
}