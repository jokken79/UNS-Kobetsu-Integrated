/**
 * Tests for React components
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { StatusBadge } from '@/components/kobetsu/StatusBadge'
import { KobetsuStats } from '@/components/kobetsu/KobetsuStats'
import type { KobetsuStats as StatsType } from '@/types'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
  useMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => children,
}))

describe('StatusBadge Component', () => {
  it('should render correct label and styling for active status', () => {
    render(<StatusBadge status="active" />)

    const badge = screen.getByText('有効')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge-active')
  })

  it('should render correct label and styling for draft status', () => {
    render(<StatusBadge status="draft" />)

    const badge = screen.getByText('下書き')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge-draft')
  })

  it('should render correct label and styling for expired status', () => {
    render(<StatusBadge status="expired" />)

    const badge = screen.getByText('期限切れ')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge-expired')
  })

  it('should render correct label and styling for cancelled status', () => {
    render(<StatusBadge status="cancelled" />)

    const badge = screen.getByText('キャンセル')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge-cancelled')
  })

  it('should render correct label and styling for renewed status', () => {
    render(<StatusBadge status="renewed" />)

    const badge = screen.getByText('更新済み')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge-renewed')
  })

  it('should handle unknown status gracefully', () => {
    render(<StatusBadge status="unknown" />)

    const badge = screen.getByText('unknown')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('badge bg-gray-100 text-gray-800')
  })
})

describe('KobetsuStats Component', () => {
  const mockStats: StatsType = {
    total_contracts: 50,
    active_contracts: 30,
    expired_contracts: 10,
    draft_contracts: 5,
    expiring_soon: 3,
    total_workers: 150,
  }

  it('should display all stat cards with correct values', () => {
    render(<KobetsuStats stats={mockStats} isLoading={false} />)

    // Check if all values are displayed
    expect(screen.getByText('50')).toBeInTheDocument() // total_contracts
    expect(screen.getByText('30')).toBeInTheDocument() // active_contracts
    expect(screen.getByText('10')).toBeInTheDocument() // expired_contracts
    expect(screen.getByText('5')).toBeInTheDocument()  // draft_contracts
    expect(screen.getByText('3')).toBeInTheDocument()  // expiring_soon
    expect(screen.getByText('150')).toBeInTheDocument() // total_workers

    // Check if all labels are displayed
    expect(screen.getByText('総契約数')).toBeInTheDocument()
    expect(screen.getByText('有効な契約')).toBeInTheDocument()
    expect(screen.getByText('期限間近')).toBeInTheDocument()
    expect(screen.getByText('下書き')).toBeInTheDocument()
    expect(screen.getByText('期限切れ')).toBeInTheDocument()
    expect(screen.getByText('派遣労働者数')).toBeInTheDocument()
  })

  it('should format large numbers with commas', () => {
    const largeStats: StatsType = {
      total_contracts: 1500,
      active_contracts: 1200,
      expired_contracts: 100,
      draft_contracts: 50,
      expiring_soon: 25,
      total_workers: 5000,
    }

    render(<KobetsuStats stats={largeStats} isLoading={false} />)

    expect(screen.getByText('1,500')).toBeInTheDocument()
    expect(screen.getByText('1,200')).toBeInTheDocument()
    expect(screen.getByText('5,000')).toBeInTheDocument()
  })

  it('should show loading skeletons when isLoading is true', () => {
    const { container } = render(<KobetsuStats isLoading={true} />)

    // Check for skeleton elements
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons.length).toBeGreaterThan(0)

    // Should not show actual values when loading
    expect(screen.queryByText('総契約数')).not.toBeInTheDocument()
  })

  it('should handle undefined stats gracefully', () => {
    render(<KobetsuStats stats={undefined} isLoading={false} />)

    // Should display zeros when stats is undefined
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBe(6) // One for each stat card
  })

  it('should highlight cards with warning conditions', () => {
    const statsWithWarnings: StatsType = {
      total_contracts: 50,
      active_contracts: 30,
      expired_contracts: 5,
      draft_contracts: 5,
      expiring_soon: 3,
      total_workers: 150,
    }

    const { container } = render(<KobetsuStats stats={statsWithWarnings} isLoading={false} />)

    // Cards with expiring_soon > 0 or expired_contracts > 0 should have highlight
    const highlightedCards = container.querySelectorAll('.ring-2.ring-amber-400')
    expect(highlightedCards.length).toBeGreaterThan(0)
  })

  it('should show warning indicator for expiring soon contracts', () => {
    const statsWithExpiring: StatsType = {
      total_contracts: 50,
      active_contracts: 30,
      expired_contracts: 0,
      draft_contracts: 5,
      expiring_soon: 3,
      total_workers: 150,
    }

    const { container } = render(<KobetsuStats stats={statsWithExpiring} isLoading={false} />)

    // Should show animated ping indicator for expiring soon
    const pingIndicator = container.querySelector('.animate-ping')
    expect(pingIndicator).toBeInTheDocument()
  })

  it('should apply hover effects to stat cards', () => {
    const { container } = render(<KobetsuStats stats={mockStats} isLoading={false} />)

    // Check for hover classes
    const cards = container.querySelectorAll('.hover\\:shadow-lg')
    expect(cards.length).toBe(6) // One for each stat

    // Check for hover transform effect
    const transformCards = container.querySelectorAll('.hover\\:-translate-y-1')
    expect(transformCards.length).toBe(6)
  })

  it('should have correct gradient colors for each stat type', () => {
    const { container } = render(<KobetsuStats stats={mockStats} isLoading={false} />)

    // Check for gradient backgrounds on icons
    const blueGradient = container.querySelector('.from-blue-500.to-blue-600')
    const emeraldGradient = container.querySelector('.from-emerald-500.to-emerald-600')
    const amberGradient = container.querySelector('.from-amber-400.to-orange-500')
    const slateGradient = container.querySelector('.from-slate-500.to-slate-600')
    const roseGradient = container.querySelector('.from-rose-500.to-red-600')
    const violetGradient = container.querySelector('.from-violet-500.to-purple-600')

    expect(blueGradient).toBeInTheDocument()
    expect(emeraldGradient).toBeInTheDocument()
    expect(amberGradient).toBeInTheDocument()
    expect(slateGradient).toBeInTheDocument()
    expect(roseGradient).toBeInTheDocument()
    expect(violetGradient).toBeInTheDocument()
  })

  it('should apply staggered animation delays', () => {
    const { container } = render(<KobetsuStats stats={mockStats} isLoading={false} />)

    const cards = container.querySelectorAll('.animate-slide-up')
    expect(cards.length).toBe(6)

    // Check that animation delays are set
    cards.forEach((card, index) => {
      const style = card.getAttribute('style')
      expect(style).toContain(`animation-delay: ${index * 50}ms`)
    })
  })
})

describe('KobetsuTable Component', () => {
  // Mock implementation since we don't have the actual component
  const MockKobetsuTable = ({ contracts }: { contracts: any[] }) => (
    <table>
      <thead>
        <tr>
          <th>契約番号</th>
          <th>派遣先</th>
          <th>開始日</th>
          <th>終了日</th>
          <th>人数</th>
          <th>ステータス</th>
        </tr>
      </thead>
      <tbody>
        {contracts.map((contract) => (
          <tr key={contract.id}>
            <td>{contract.contract_number}</td>
            <td>{contract.worksite_name}</td>
            <td>{contract.dispatch_start_date}</td>
            <td>{contract.dispatch_end_date}</td>
            <td>{contract.number_of_workers}</td>
            <td><StatusBadge status={contract.status} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  )

  it('should render contract data in table format', () => {
    const mockContracts = [
      {
        id: 1,
        contract_number: 'KOB-202411-0001',
        worksite_name: 'テスト株式会社',
        dispatch_start_date: '2024-12-01',
        dispatch_end_date: '2025-11-30',
        number_of_workers: 5,
        status: 'active',
      },
      {
        id: 2,
        contract_number: 'KOB-202411-0002',
        worksite_name: 'サンプル工場',
        dispatch_start_date: '2024-12-15',
        dispatch_end_date: '2025-12-14',
        number_of_workers: 3,
        status: 'draft',
      },
    ]

    render(<MockKobetsuTable contracts={mockContracts} />)

    // Check headers
    expect(screen.getByText('契約番号')).toBeInTheDocument()
    expect(screen.getByText('派遣先')).toBeInTheDocument()
    expect(screen.getByText('開始日')).toBeInTheDocument()
    expect(screen.getByText('終了日')).toBeInTheDocument()
    expect(screen.getByText('人数')).toBeInTheDocument()
    expect(screen.getByText('ステータス')).toBeInTheDocument()

    // Check first contract data
    expect(screen.getByText('KOB-202411-0001')).toBeInTheDocument()
    expect(screen.getByText('テスト株式会社')).toBeInTheDocument()
    expect(screen.getByText('2024-12-01')).toBeInTheDocument()
    expect(screen.getByText('2025-11-30')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()

    // Check second contract data
    expect(screen.getByText('KOB-202411-0002')).toBeInTheDocument()
    expect(screen.getByText('サンプル工場')).toBeInTheDocument()
    expect(screen.getByText('2024-12-15')).toBeInTheDocument()
    expect(screen.getByText('2025-12-14')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('should handle empty contract list', () => {
    render(<MockKobetsuTable contracts={[]} />)

    // Should still show headers
    expect(screen.getByText('契約番号')).toBeInTheDocument()

    // Should not have any contract rows
    const rows = screen.queryAllByRole('row')
    expect(rows.length).toBe(1) // Only header row
  })
})

describe('Form Validation', () => {
  it('should validate required fields', () => {
    const validateForm = (data: any) => {
      const errors: Record<string, string> = {}

      if (!data.worksite_name) {
        errors.worksite_name = '派遣先名を入力してください'
      }
      if (!data.work_content || data.work_content.length < 10) {
        errors.work_content = '業務内容を10文字以上で入力してください'
      }
      if (!data.dispatch_start_date) {
        errors.dispatch_start_date = '開始日を入力してください'
      }
      if (!data.dispatch_end_date) {
        errors.dispatch_end_date = '終了日を入力してください'
      }
      if (!data.supervisor_name) {
        errors.supervisor_name = '監督者名を入力してください'
      }

      return errors
    }

    const emptyForm = {
      worksite_name: '',
      work_content: '',
      dispatch_start_date: '',
      dispatch_end_date: '',
      supervisor_name: '',
    }

    const errors = validateForm(emptyForm)

    expect(errors.worksite_name).toBe('派遣先名を入力してください')
    expect(errors.work_content).toBe('業務内容を10文字以上で入力してください')
    expect(errors.dispatch_start_date).toBe('開始日を入力してください')
    expect(errors.dispatch_end_date).toBe('終了日を入力してください')
    expect(errors.supervisor_name).toBe('監督者名を入力してください')
  })

  it('should validate date order', () => {
    const validateDates = (startDate: string, endDate: string) => {
      if (endDate < startDate) {
        return '終了日は開始日より後でなければなりません'
      }
      return null
    }

    const invalidDateError = validateDates('2025-12-01', '2025-01-01')
    expect(invalidDateError).toBe('終了日は開始日より後でなければなりません')

    const validDateError = validateDates('2025-01-01', '2025-12-01')
    expect(validDateError).toBeNull()
  })

  it('should validate work days selection', () => {
    const validateWorkDays = (selectedDays: string[]) => {
      const validDays = ['月', '火', '水', '木', '金', '土', '日']
      const errors: string[] = []

      if (selectedDays.length === 0) {
        errors.push('少なくとも1つの勤務日を選択してください')
      }

      const invalidDays = selectedDays.filter(day => !validDays.includes(day))
      if (invalidDays.length > 0) {
        errors.push(`無効な曜日: ${invalidDays.join(', ')}`)
      }

      return errors
    }

    const emptyDaysErrors = validateWorkDays([])
    expect(emptyDaysErrors).toContain('少なくとも1つの勤務日を選択してください')

    const invalidDaysErrors = validateWorkDays(['月', 'Monday', 'Tuesday'])
    expect(invalidDaysErrors).toContain('無効な曜日: Monday, Tuesday')

    const validDaysErrors = validateWorkDays(['月', '火', '水', '木', '金'])
    expect(validDaysErrors.length).toBe(0)
  })

  it('should validate hourly rate', () => {
    const validateHourlyRate = (rate: number) => {
      if (rate < 800) {
        return '時給は最低賃金以上でなければなりません'
      }
      if (rate > 10000) {
        return '時給が高すぎます。確認してください'
      }
      return null
    }

    expect(validateHourlyRate(500)).toBe('時給は最低賃金以上でなければなりません')
    expect(validateHourlyRate(15000)).toBe('時給が高すぎます。確認してください')
    expect(validateHourlyRate(1500)).toBeNull()
  })
})