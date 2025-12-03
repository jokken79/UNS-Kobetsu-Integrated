'use client'

import { useState } from 'react'
import { LineCard } from '@/components/factory'
import type { FactoryLineResponse, EmployeeResponse } from '@/types'

// Mock data for demonstration
const mockLine: FactoryLineResponse = {
  id: 1,
  factory_id: 1,
  line_id: 'LINE-001',
  department: '製造1課',
  line_name: 'Aライン',
  supervisor_department: '製造部',
  supervisor_position: '課長',
  supervisor_name: '山田太郎',
  supervisor_phone: '090-1234-5678',
  job_description: '製品の組立作業、検査作業',
  job_description_detail: '自動車部品の組立作業、目視検査、梱包作業。立ち作業が中心で、重量物の取り扱いあり（最大10kg）。',
  responsibility_level: '一般作業員',
  hourly_rate: 1500,
  billing_rate: 2100,
  overtime_rate: 1875,
  night_rate: 1875,
  holiday_rate: 2025,
  is_active: true,
  display_order: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z'
}

const mockEmployees: EmployeeResponse[] = [
  {
    id: 1,
    employee_number: '1001',
    hakenmoto_id: 'HM-1001',
    rirekisho_id: 'RK-1001',
    full_name_kanji: 'グエン・バン・ナム',
    full_name_kana: 'グエン バン ナム',
    full_name_romaji: 'Nguyen Van Nam',
    gender: '男性',
    date_of_birth: '1990-05-15',
    nationality: 'ベトナム',
    postal_code: '123-4567',
    address: '東京都新宿区...',
    phone: '03-1234-5678',
    mobile: '090-1234-5678',
    email: 'nguyen@example.com',
    emergency_contact_name: 'グエン・ティ・ラン',
    emergency_contact_phone: '090-9876-5432',
    emergency_contact_relationship: '妻',
    hire_date: '2021-04-01',
    termination_date: null,
    termination_reason: null,
    status: 'active',
    contract_type: '有期雇用',
    employment_type: '派遣',
    factory_id: 1,
    factory_line_id: 1,
    company_name: '株式会社ABC工業',
    plant_name: '第一工場',
    department: '製造1課',
    line_name: 'Aライン',
    position: '作業員',
    hourly_rate: 1650,  // Above base rate
    billing_rate: 2200,
    transportation_allowance: 10000,
    visa_type: '技能実習',
    visa_expiry_date: '2025-03-31',
    zairyu_card_number: 'AB12345678',
    passport_number: 'P12345678',
    has_employment_insurance: true,
    has_health_insurance: true,
    has_pension_insurance: true,
    yukyu_total: 10,
    yukyu_used: 3,
    yukyu_remaining: 7,
    apartment_name: 'サンハイツ',
    apartment_room: '201',
    apartment_rent: 50000,
    is_corporate_housing: true,
    bank_name: '三菱UFJ銀行',
    bank_branch: '新宿支店',
    bank_account_type: '普通',
    bank_account_number: '1234567',
    bank_account_holder: 'グエン バン ナム',
    notes: null,
    age: 34,
    display_name: 'グエン バン ナム',
    age_category: '18歳以上60歳未満',
    is_indefinite_employment: false,
    employment_type_display: '派遣労働者',
    created_at: '2021-04-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z'
  },
  {
    id: 2,
    employee_number: '1045',
    hakenmoto_id: 'HM-1045',
    rirekisho_id: 'RK-1045',
    full_name_kanji: 'レ・ティ・ホア',
    full_name_kana: 'レ ティ ホア',
    full_name_romaji: 'Le Thi Hoa',
    gender: '女性',
    date_of_birth: '1995-08-20',
    nationality: 'ベトナム',
    postal_code: '123-4567',
    address: '東京都新宿区...',
    phone: '03-1234-5678',
    mobile: '090-2345-6789',
    email: 'le@example.com',
    emergency_contact_name: 'レ・バン・タン',
    emergency_contact_phone: '090-8765-4321',
    emergency_contact_relationship: '夫',
    hire_date: '2022-01-01',
    termination_date: null,
    termination_reason: null,
    status: 'active',
    contract_type: '有期雇用',
    employment_type: '派遣',
    factory_id: 1,
    factory_line_id: 1,
    company_name: '株式会社ABC工業',
    plant_name: '第一工場',
    department: '製造1課',
    line_name: 'Aライン',
    position: '作業員',
    hourly_rate: 1600,  // Above base rate
    billing_rate: 2150,
    transportation_allowance: 10000,
    visa_type: '技能実習',
    visa_expiry_date: '2025-12-31',
    zairyu_card_number: 'CD12345678',
    passport_number: 'P87654321',
    has_employment_insurance: true,
    has_health_insurance: true,
    has_pension_insurance: true,
    yukyu_total: 10,
    yukyu_used: 1,
    yukyu_remaining: 9,
    apartment_name: 'サンハイツ',
    apartment_room: '203',
    apartment_rent: 50000,
    is_corporate_housing: true,
    bank_name: '三菱UFJ銀行',
    bank_branch: '新宿支店',
    bank_account_type: '普通',
    bank_account_number: '7654321',
    bank_account_holder: 'レ ティ ホア',
    notes: null,
    age: 29,
    display_name: 'レ ティ ホア',
    age_category: '18歳以上60歳未満',
    is_indefinite_employment: false,
    employment_type_display: '派遣労働者',
    created_at: '2022-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z'
  },
  {
    id: 3,
    employee_number: '1089',
    hakenmoto_id: 'HM-1089',
    rirekisho_id: 'RK-1089',
    full_name_kanji: 'ファン・ミン・トゥアン',
    full_name_kana: 'ファン ミン トゥアン',
    full_name_romaji: 'Phan Minh Tuan',
    gender: '男性',
    date_of_birth: '1998-03-10',
    nationality: 'ベトナム',
    postal_code: '123-4567',
    address: '東京都新宿区...',
    phone: '03-1234-5678',
    mobile: '090-3456-7890',
    email: 'phan@example.com',
    emergency_contact_name: 'ファン・ティ・リン',
    emergency_contact_phone: '090-7654-3210',
    emergency_contact_relationship: '母',
    hire_date: '2023-06-01',
    termination_date: null,
    termination_reason: null,
    status: 'active',
    contract_type: '有期雇用',
    employment_type: '派遣',
    factory_id: 1,
    factory_line_id: 1,
    company_name: '株式会社ABC工業',
    plant_name: '第一工場',
    department: '製造1課',
    line_name: 'Aライン',
    position: '作業員',
    hourly_rate: 1500,  // Base rate (no individual override)
    billing_rate: 2100,
    transportation_allowance: 10000,
    visa_type: '技能実習',
    visa_expiry_date: '2026-05-31',
    zairyu_card_number: 'EF12345678',
    passport_number: 'P11223344',
    has_employment_insurance: true,
    has_health_insurance: true,
    has_pension_insurance: true,
    yukyu_total: 10,
    yukyu_used: 0,
    yukyu_remaining: 10,
    apartment_name: 'グリーンハイツ',
    apartment_room: '105',
    apartment_rent: 45000,
    is_corporate_housing: true,
    bank_name: '三井住友銀行',
    bank_branch: '渋谷支店',
    bank_account_type: '普通',
    bank_account_number: '2345678',
    bank_account_holder: 'ファン ミン トゥアン',
    notes: null,
    age: 26,
    display_name: 'ファン ミン トゥアン',
    age_category: '18歳以上60歳未満',
    is_indefinite_employment: false,
    employment_type_display: '派遣労働者',
    created_at: '2023-06-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z'
  },
  {
    id: 4,
    employee_number: '1102',
    hakenmoto_id: 'HM-1102',
    rirekisho_id: 'RK-1102',
    full_name_kanji: 'チャン・ホア・リン',
    full_name_kana: 'チャン ホア リン',
    full_name_romaji: 'Tran Hoa Linh',
    gender: '女性',
    date_of_birth: '2000-11-25',
    nationality: 'ベトナム',
    postal_code: '123-4567',
    address: '東京都新宿区...',
    phone: '03-1234-5678',
    mobile: '090-4567-8901',
    email: 'tran@example.com',
    emergency_contact_name: 'チャン・バン・ドゥック',
    emergency_contact_phone: '090-6543-2109',
    emergency_contact_relationship: '父',
    hire_date: '2024-01-01',
    termination_date: null,
    termination_reason: null,
    status: 'active',
    contract_type: '有期雇用',
    employment_type: '派遣',
    factory_id: 1,
    factory_line_id: 1,
    company_name: '株式会社ABC工業',
    plant_name: '第一工場',
    department: '製造1課',
    line_name: 'Aライン',
    position: '作業員',
    hourly_rate: null,  // Will use line base rate
    billing_rate: null,
    transportation_allowance: 10000,
    visa_type: '技能実習',
    visa_expiry_date: '2027-01-31',
    zairyu_card_number: 'GH12345678',
    passport_number: 'P55667788',
    has_employment_insurance: true,
    has_health_insurance: true,
    has_pension_insurance: true,
    yukyu_total: 0,
    yukyu_used: 0,
    yukyu_remaining: 0,
    apartment_name: 'グリーンハイツ',
    apartment_room: '203',
    apartment_rent: 45000,
    is_corporate_housing: true,
    bank_name: 'みずほ銀行',
    bank_branch: '池袋支店',
    bank_account_type: '普通',
    bank_account_number: '3456789',
    bank_account_holder: 'チャン ホア リン',
    notes: null,
    age: 24,
    display_name: 'チャン ホア リン',
    age_category: '18歳以上60歳未満',
    is_indefinite_employment: false,
    employment_type_display: '派遣労働者',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z'
  },
  {
    id: 5,
    employee_number: '1115',
    hakenmoto_id: 'HM-1115',
    rirekisho_id: 'RK-1115',
    full_name_kanji: 'ブイ・タン・ロン',
    full_name_kana: 'ブイ タン ロン',
    full_name_romaji: 'Bui Thanh Long',
    gender: '男性',
    date_of_birth: '1999-07-12',
    nationality: 'ベトナム',
    postal_code: '123-4567',
    address: '東京都新宿区...',
    phone: '03-1234-5678',
    mobile: '090-5678-9012',
    email: 'bui@example.com',
    emergency_contact_name: 'ブイ・ティ・マイ',
    emergency_contact_phone: '090-5432-1098',
    emergency_contact_relationship: '姉',
    hire_date: '2024-03-01',
    termination_date: null,
    termination_reason: null,
    status: 'active',
    contract_type: '有期雇用',
    employment_type: '派遣',
    factory_id: 1,
    factory_line_id: 1,
    company_name: '株式会社ABC工業',
    plant_name: '第一工場',
    department: '製造1課',
    line_name: 'Aライン',
    position: '作業員',
    hourly_rate: 1500,
    billing_rate: 2100,
    transportation_allowance: 10000,
    visa_type: '技能実習',
    visa_expiry_date: '2027-02-28',
    zairyu_card_number: 'IJ12345678',
    passport_number: 'P99887766',
    has_employment_insurance: true,
    has_health_insurance: true,
    has_pension_insurance: true,
    yukyu_total: 0,
    yukyu_used: 0,
    yukyu_remaining: 0,
    apartment_name: 'サンライズ',
    apartment_room: '302',
    apartment_rent: 48000,
    is_corporate_housing: true,
    bank_name: 'りそな銀行',
    bank_branch: '新宿支店',
    bank_account_type: '普通',
    bank_account_number: '4567890',
    bank_account_holder: 'ブイ タン ロン',
    notes: null,
    age: 25,
    display_name: 'ブイ タン ロン',
    age_category: '18歳以上60歳未満',
    is_indefinite_employment: false,
    employment_type_display: '派遣労働者',
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-15T00:00:00Z'
  }
]

const mockLineNoSupervisor: FactoryLineResponse = {
  id: 2,
  factory_id: 1,
  line_id: 'LINE-002',
  department: '製造2課',
  line_name: 'Bライン',
  supervisor_department: null,
  supervisor_position: null,
  supervisor_name: null,
  supervisor_phone: null,
  job_description: '梱包作業',
  job_description_detail: null,
  responsibility_level: '一般作業員',
  hourly_rate: 1400,
  billing_rate: 1950,
  overtime_rate: 1750,
  night_rate: null,
  holiday_rate: null,
  is_active: true,
  display_order: 2,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z'
}

export default function LineCardDemoPage() {
  const [expandedCards, setExpandedCards] = useState<{ [key: number]: boolean }>({
    1: true,
    2: false,
    3: true
  })

  const handleEdit = (lineId: number) => {
    console.log('Edit line:', lineId)
    alert(`Edit line ${lineId}`)
  }

  const handleDelete = (lineId: number) => {
    console.log('Delete line:', lineId)
    // The component will handle confirmation dialog
  }

  const toggleExpand = (lineId: number) => {
    setExpandedCards(prev => ({
      ...prev,
      [lineId]: !prev[lineId]
    }))
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">LineCard Component Demo</h1>
      <p className="text-gray-600 mb-8">Production line cards with supervisor information and employee assignments</p>

      <div className="space-y-6">
        {/* Card with full data */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Full Data Example</h2>
          <LineCard
            line={mockLine}
            employees={mockEmployees}
            baseRate={1500}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isExpanded={expandedCards[1]}
            onToggleExpand={() => toggleExpand(1)}
          />
        </div>

        {/* Card with no supervisor */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">No Supervisor Example</h2>
          <LineCard
            line={mockLineNoSupervisor}
            employees={mockEmployees.slice(0, 2)}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isExpanded={expandedCards[2]}
            onToggleExpand={() => toggleExpand(2)}
          />
        </div>

        {/* Card with no employees */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Empty Line Example</h2>
          <LineCard
            line={{
              ...mockLine,
              id: 3,
              line_name: 'Cライン',
              department: '製造3課'
            }}
            employees={[]}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isExpanded={expandedCards[3]}
            onToggleExpand={() => toggleExpand(3)}
          />
        </div>

        {/* Interaction Examples */}
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>• Click the header or arrow to expand/collapse the card</li>
            <li>• Green ↑ indicator shows employees with rates above the base rate</li>
            <li>• Employees are sorted by hourly rate (highest first)</li>
            <li>• Edit button triggers onEdit callback</li>
            <li>• Delete button shows confirmation dialog before deletion</li>
            <li>• Purple accent color distinguishes line cards from factory cards</li>
            <li>• Responsive layout adapts to different screen sizes</li>
            <li>• Empty state shows when no employees are assigned</li>
          </ul>
        </div>
      </div>
    </div>
  )
}