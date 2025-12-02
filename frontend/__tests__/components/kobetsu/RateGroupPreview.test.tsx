import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RateGroupPreview } from '@/components/kobetsu/RateGroupPreview'

describe('RateGroupPreview', () => {
  const mockGroups = [
    {
      hourly_rate: 1650,
      billing_rate: 2100,
      employee_count: 2,
      employees: [
        {
          id: 1,
          employee_number: '1001',
          full_name_kanji: 'テスト太郎',
          full_name_kana: 'テストタロウ',
          department: '製造部',
          line_name: 'Aライン'
        },
        {
          id: 2,
          employee_number: '1002',
          full_name_kanji: 'テスト花子',
          full_name_kana: 'テストハナコ',
          department: '製造部',
          line_name: 'Aライン'
        }
      ]
    },
    {
      hourly_rate: 1600,
      billing_rate: 2050,
      employee_count: 1,
      employees: [
        {
          id: 3,
          employee_number: '1003',
          full_name_kana: 'サンプルジロウ',
          department: '製造部',
          line_name: 'Bライン'
        }
      ]
    }
  ]

  const defaultProps = {
    groups: mockGroups,
    totalEmployees: 3,
    hasMultipleRates: true,
    suggestedContracts: 2,
    message: '3名を2つの契約に分割することを推奨します',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    isLoading: false
  }

  it('renders the component with groups', () => {
    render(<RateGroupPreview {...defaultProps} />)

    // Check header
    expect(screen.getByText('単価別グループプレビュー')).toBeInTheDocument()

    // Check warning message
    expect(screen.getByText('3名を2つの契約に分割することを推奨します')).toBeInTheDocument()

    // Check group headers
    expect(screen.getByText(/契約 #1:/)).toBeInTheDocument()
    expect(screen.getByText(/契約 #2:/)).toBeInTheDocument()

    // Check employee count badges
    expect(screen.getByText('2名')).toBeInTheDocument()
    expect(screen.getByText('1名')).toBeInTheDocument()

    // Check employee names
    expect(screen.getByText('テスト太郎')).toBeInTheDocument()
    expect(screen.getByText('テスト花子')).toBeInTheDocument()
    expect(screen.getByText('サンプルジロウ')).toBeInTheDocument()
  })

  it('shows radio options when multiple rates exist', () => {
    render(<RateGroupPreview {...defaultProps} />)

    const singleOption = screen.getByLabelText('1つの契約として作成（全員同じ単価を適用）')
    const splitOption = screen.getByLabelText('2つの契約に分割して作成（推奨）')

    expect(singleOption).toBeInTheDocument()
    expect(splitOption).toBeInTheDocument()

    // Default should be split when hasMultipleRates is true
    expect(splitOption).toBeChecked()
    expect(singleOption).not.toBeChecked()
  })

  it('hides radio options when single rate', () => {
    const singleRateProps = {
      ...defaultProps,
      hasMultipleRates: false,
      suggestedContracts: 1
    }
    render(<RateGroupPreview {...singleRateProps} />)

    expect(screen.queryByLabelText('1つの契約として作成（全員同じ単価を適用）')).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/つの契約に分割して作成/)).not.toBeInTheDocument()
  })

  it('calls onConfirm with split decision', async () => {
    const onConfirm = vi.fn()
    render(<RateGroupPreview {...defaultProps} onConfirm={onConfirm} />)

    // Change to single contract option
    const singleOption = screen.getByLabelText('1つの契約として作成（全員同じ単価を適用）')
    fireEvent.click(singleOption)

    // Click confirm
    const confirmButton = screen.getByText('契約を作成')
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledWith(false)
    })
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<RateGroupPreview {...defaultProps} onCancel={onCancel} />)

    const cancelButton = screen.getByText('キャンセル')
    fireEvent.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('calls onCancel when backdrop clicked', () => {
    const onCancel = vi.fn()
    const { container } = render(<RateGroupPreview {...defaultProps} onCancel={onCancel} />)

    // Click the backdrop
    const backdrop = container.querySelector('.bg-gray-500.bg-opacity-75')
    if (backdrop) {
      fireEvent.click(backdrop)
    }

    expect(onCancel).toHaveBeenCalled()
  })

  it('shows loading state', () => {
    render(<RateGroupPreview {...defaultProps} isLoading={true} />)

    expect(screen.getByText('処理中...')).toBeInTheDocument()

    // Buttons should be disabled
    const confirmButton = screen.getByText('処理中...').closest('button')
    const cancelButton = screen.getByText('キャンセル')

    expect(confirmButton).toBeDisabled()
    expect(cancelButton).toBeDisabled()
  })

  it('formats currency correctly', () => {
    render(<RateGroupPreview {...defaultProps} />)

    // Check if hourly rates are formatted as currency (Intl uses full-width yen ￥)
    expect(screen.getByText(/[¥￥]1,650/)).toBeInTheDocument()
    expect(screen.getByText(/[¥￥]1,600/)).toBeInTheDocument()
  })

  it('handles Escape key to close', () => {
    const onCancel = vi.fn()
    render(<RateGroupPreview {...defaultProps} onCancel={onCancel} />)

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onCancel).toHaveBeenCalled()
  })

  it('handles Ctrl+Enter to confirm', () => {
    const onConfirm = vi.fn()
    render(<RateGroupPreview {...defaultProps} onConfirm={onConfirm} />)

    fireEvent.keyDown(document, { key: 'Enter', ctrlKey: true })

    expect(onConfirm).toHaveBeenCalledWith(true) // Default is split when hasMultipleRates
  })

  it('displays both kanji and kana names when available', () => {
    render(<RateGroupPreview {...defaultProps} />)

    // Employee with kanji should show both
    expect(screen.getByText('テスト太郎')).toBeInTheDocument()
    expect(screen.getByText('テストタロウ')).toBeInTheDocument()

    // Employee with only kana should show kana
    expect(screen.getByText('サンプルジロウ')).toBeInTheDocument()
  })

  it('handles missing department and line gracefully', () => {
    const groupsWithMissingData = [
      {
        hourly_rate: 1500,
        employee_count: 1,
        employees: [
          {
            id: 4,
            employee_number: '1004',
            full_name_kana: 'テスト',
            // department and line_name are undefined
          }
        ]
      }
    ]

    render(<RateGroupPreview {...defaultProps} groups={groupsWithMissingData} />)

    // Should show "-" for missing values
    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThan(0)
  })
})