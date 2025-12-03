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

interface EmployeesByFactoryChartProps {
  className?: string
}

export function EmployeesByFactoryChart({ className = '' }: EmployeesByFactoryChartProps) {
  // Mock data - in production, this would come from API
  const factoryData = [
    { name: '豊田自動車 豊田工場', employees: 85 },
    { name: '高雄工業 静岡工場', employees: 62 },
    { name: '中部製造 名古屋工場', employees: 48 },
    { name: '東海精密 岐阜工場', employees: 35 },
    { name: 'アイシン精機 三河工場', employees: 28 },
  ]

  const data = {
    labels: factoryData.map(f => f.name),
    datasets: [
      {
        label: '従業員数',
        data: factoryData.map(f => f.employees),
        backgroundColor: 'rgb(147, 51, 234)',  // purple-600
        borderColor: 'rgb(147, 51, 234)',
        borderWidth: 0,
        borderRadius: 6,
        barPercentage: 0.7,
      },
    ],
  }

  const options: ChartOptions<'bar'> = {
    indexAxis: 'y',
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
            return `${context.parsed.x} 名`
          },
        },
      },
    },
    scales: {
      x: {
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
          stepSize: 20,
          callback: function(value) {
            return value + '名'
          },
        },
      },
      y: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 12,
          },
          color: '#4b5563',
          padding: 8,
          callback: function(value, index) {
            const label = this.getLabelForValue(index as number)
            // Truncate long factory names
            if (label && label.length > 20) {
              return label.substring(0, 20) + '...'
            }
            return label
          },
        },
      },
    },
    layout: {
      padding: {
        left: 0,
        right: 10,
      },
    },
  }

  return (
    <div className={`${className}`}>
      <Bar data={data} options={options} />
    </div>
  )
}