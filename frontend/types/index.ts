/**
 * TypeScript type definitions for UNS Kobetsu Keiyakusho
 */

// Contact Info
export interface ContactInfo {
  department: string
  position: string
  name: string
  phone: string
}

// Manager Info
export interface ManagerInfo {
  department: string
  position: string
  name: string
  phone: string
  license_number?: string
}

// Kobetsu Keiyakusho Create
export interface KobetsuCreate {
  factory_id: number
  dispatch_assignment_id?: number
  employee_ids: number[]
  contract_date: string
  dispatch_start_date: string
  dispatch_end_date: string
  work_content: string
  responsibility_level: string
  worksite_name: string
  worksite_address: string
  organizational_unit?: string
  supervisor_department: string
  supervisor_position: string
  supervisor_name: string
  work_days: string[]
  work_start_time: string
  work_end_time: string
  break_time_minutes: number
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_days_month?: number
  holiday_work_max_days?: number
  safety_measures?: string
  haken_moto_complaint_contact: ContactInfo
  haken_saki_complaint_contact: ContactInfo
  hourly_rate: number
  overtime_rate: number
  night_shift_rate?: number
  holiday_rate?: number
  welfare_facilities?: string[]
  haken_moto_manager: ManagerInfo
  haken_saki_manager: ManagerInfo
  termination_measures?: string
  is_kyotei_taisho?: boolean
  is_direct_hire_prevention?: boolean
  is_mukeiko_60over_only?: boolean
  notes?: string
}

// Kobetsu Keiyakusho Update
export interface KobetsuUpdate {
  contract_date?: string
  dispatch_end_date?: string
  work_content?: string
  responsibility_level?: string
  supervisor_name?: string
  work_days?: string[]
  hourly_rate?: number
  overtime_rate?: number
  status?: string
  notes?: string
}

// Kobetsu Keiyakusho Response
export interface KobetsuResponse {
  id: number
  factory_id: number
  dispatch_assignment_id?: number
  contract_number: string
  contract_date: string
  dispatch_start_date: string
  dispatch_end_date: string
  work_content: string
  responsibility_level: string
  worksite_name: string
  worksite_address: string
  organizational_unit?: string
  supervisor_department: string
  supervisor_position: string
  supervisor_name: string
  work_days: string[]
  work_start_time: string
  work_end_time: string
  break_time_minutes: number
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_days_month?: number
  holiday_work_max_days?: number
  safety_measures?: string
  haken_moto_complaint_contact: ContactInfo
  haken_saki_complaint_contact: ContactInfo
  hourly_rate: number
  overtime_rate: number
  night_shift_rate?: number
  holiday_rate?: number
  welfare_facilities?: string[]
  haken_moto_manager: ManagerInfo
  haken_saki_manager: ManagerInfo
  termination_measures?: string
  is_kyotei_taisho: boolean
  is_direct_hire_prevention: boolean
  is_mukeiko_60over_only: boolean
  number_of_workers: number
  status: string
  pdf_path?: string
  signed_date?: string
  notes?: string
  created_at: string
  updated_at: string
  created_by?: number
  employees?: KobetsuEmployeeInfo[]
}

// Kobetsu List Item
export interface KobetsuListItem {
  id: number
  contract_number: string
  worksite_name: string
  dispatch_start_date: string
  dispatch_end_date: string
  number_of_workers: number
  status: string
  created_at: string
}

// Kobetsu Stats
export interface KobetsuStats {
  total_contracts: number
  active_contracts: number
  expiring_soon: number
  expired_contracts: number
  draft_contracts: number
  total_workers: number
}

// Employee Basic Info (nested in KobetsuEmployeeInfo)
export interface EmployeeBasicInfo {
  id: number
  employee_number: string  // 社員№
  full_name_kanji?: string  // 漢字氏名
  full_name_kana?: string  // カナ氏名
  full_name_romaji?: string  // ローマ字氏名
  nationality?: string  // 国籍
}

// Kobetsu Employee Info (join table info with nested employee)
export interface KobetsuEmployeeInfo {
  id: number  // KobetsuEmployee.id
  employee_id: number  // FK to employees
  hourly_rate?: number  // 個別時給
  individual_start_date?: string  // 途中入社日
  individual_end_date?: string  // 途中退社日
  is_indefinite_employment: boolean  // 無期雇用
  employee?: EmployeeBasicInfo  // Nested employee info
}

// Paginated Response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

// Auth Types
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
}

// API List Params
export interface KobetsuListParams {
  skip?: number
  limit?: number
  status?: string
  factory_id?: number
  search?: string
  start_date?: string
  end_date?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// ========================================
// FACTORY TYPES
// ========================================

export interface FactoryLineCreate {
  line_id?: string
  department?: string
  line_name?: string
  supervisor_department?: string
  supervisor_position?: string
  supervisor_name?: string
  supervisor_phone?: string
  job_description?: string
  job_description_detail?: string
  responsibility_level?: string
  hourly_rate?: number
  billing_rate?: number
  overtime_rate?: number
  night_rate?: number
  holiday_rate?: number
  display_order?: number
}

export interface FactoryLineUpdate {
  line_id?: string
  department?: string
  line_name?: string
  supervisor_department?: string
  supervisor_position?: string
  supervisor_name?: string
  supervisor_phone?: string
  job_description?: string
  job_description_detail?: string
  responsibility_level?: string
  hourly_rate?: number
  billing_rate?: number
  overtime_rate?: number
  night_rate?: number
  holiday_rate?: number
  is_active?: boolean
  display_order?: number
}

export interface FactoryLineResponse {
  id: number
  factory_id: number
  line_id?: string
  department?: string
  line_name?: string
  supervisor_department?: string
  supervisor_position?: string
  supervisor_name?: string
  supervisor_phone?: string
  job_description?: string
  job_description_detail?: string
  responsibility_level: string
  hourly_rate?: number
  billing_rate?: number
  overtime_rate?: number
  night_rate?: number
  holiday_rate?: number
  is_active: boolean
  display_order: number
  created_at: string
  updated_at?: string
}

export interface FactoryCreate {
  factory_id?: string
  company_name: string
  company_address?: string
  company_phone?: string
  company_fax?: string
  client_responsible_department?: string
  client_responsible_name?: string
  client_responsible_phone?: string
  client_complaint_department?: string
  client_complaint_name?: string
  client_complaint_phone?: string
  plant_name: string
  plant_address?: string
  plant_phone?: string
  dispatch_responsible_department?: string
  dispatch_responsible_name?: string
  dispatch_responsible_phone?: string
  dispatch_complaint_department?: string
  dispatch_complaint_name?: string
  dispatch_complaint_phone?: string
  work_hours_description?: string
  break_time_description?: string
  calendar_description?: string
  day_shift_start?: string
  day_shift_end?: string
  night_shift_start?: string
  night_shift_end?: string
  break_minutes?: number
  overtime_description?: string
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_hours_year?: number
  overtime_special_max_month?: number
  overtime_special_count_year?: number
  holiday_work_description?: string
  holiday_work_max_days_month?: number
  conflict_date?: string
  time_unit_minutes?: number
  closing_date?: string
  payment_date?: string
  bank_account?: string
  worker_closing_date?: string
  worker_payment_date?: string
  worker_calendar?: string
  agreement_period?: string
  agreement_explainer?: string
  is_active?: boolean
  notes?: string
  lines?: FactoryLineCreate[]
}

export interface FactoryUpdate {
  company_name?: string
  company_address?: string
  company_phone?: string
  company_fax?: string
  client_responsible_department?: string
  client_responsible_name?: string
  client_responsible_phone?: string
  client_complaint_department?: string
  client_complaint_name?: string
  client_complaint_phone?: string
  plant_name?: string
  plant_address?: string
  plant_phone?: string
  dispatch_responsible_department?: string
  dispatch_responsible_name?: string
  dispatch_responsible_phone?: string
  dispatch_complaint_department?: string
  dispatch_complaint_name?: string
  dispatch_complaint_phone?: string
  work_hours_description?: string
  break_time_description?: string
  calendar_description?: string
  day_shift_start?: string
  day_shift_end?: string
  night_shift_start?: string
  night_shift_end?: string
  break_minutes?: number
  overtime_description?: string
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_hours_year?: number
  overtime_special_max_month?: number
  overtime_special_count_year?: number
  holiday_work_description?: string
  holiday_work_max_days_month?: number
  conflict_date?: string
  time_unit_minutes?: number
  closing_date?: string
  payment_date?: string
  bank_account?: string
  worker_closing_date?: string
  worker_payment_date?: string
  worker_calendar?: string
  agreement_period?: string
  agreement_explainer?: string
  is_active?: boolean
  notes?: string
}

export interface FactoryResponse {
  id: number
  factory_id: string
  company_name: string
  company_address?: string
  company_phone?: string
  company_fax?: string
  client_responsible_department?: string
  client_responsible_name?: string
  client_responsible_phone?: string
  client_complaint_department?: string
  client_complaint_name?: string
  client_complaint_phone?: string
  plant_name: string
  plant_address?: string
  plant_phone?: string
  dispatch_responsible_department?: string
  dispatch_responsible_name?: string
  dispatch_responsible_phone?: string
  dispatch_complaint_department?: string
  dispatch_complaint_name?: string
  dispatch_complaint_phone?: string
  work_hours_description?: string
  break_time_description?: string
  calendar_description?: string
  day_shift_start?: string
  day_shift_end?: string
  night_shift_start?: string
  night_shift_end?: string
  break_minutes: number
  overtime_description?: string
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_hours_year?: number
  holiday_work_description?: string
  holiday_work_max_days_month?: number
  conflict_date?: string
  closing_date?: string
  payment_date?: string
  bank_account?: string
  agreement_period?: string
  is_active: boolean
  notes?: string
  created_at: string
  updated_at?: string
  lines: FactoryLineResponse[]
  employees_count: number
}

export interface FactoryListItem {
  id: number
  factory_id: string
  company_name: string
  plant_name: string
  conflict_date?: string
  is_active: boolean
  lines_count: number
  employees_count: number
}

// Cascade dropdown types
export interface CompanyOption {
  company_name: string
  factories_count: number
}

export interface PlantOption {
  id: number
  factory_id: string
  plant_name: string
  plant_address?: string
}

export interface DepartmentOption {
  department: string
  lines_count: number
}

export interface LineOption {
  id: number
  line_id?: string
  line_name: string
  job_description?: string
  hourly_rate?: number
  supervisor_name?: string
}

export interface FactoryCascadeData {
  factory: FactoryResponse
  line: FactoryLineResponse
}

// ========================================
// EMPLOYEE TYPES
// ========================================

export interface EmployeeCreate {
  employee_number: string
  full_name_kanji: string
  full_name_kana: string
  full_name_romaji?: string
  gender?: string
  date_of_birth?: string
  age?: number
  nationality?: string
  postal_code?: string
  address?: string
  phone?: string
  mobile?: string
  email?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
  hire_date: string
  status?: string
  contract_type?: string
  employment_type?: string
  factory_id?: number
  factory_line_id?: number
  company_name?: string
  plant_name?: string
  department?: string
  line_name?: string
  position?: string
  hourly_rate?: number
  billing_rate?: number
  transportation_allowance?: number
  visa_type?: string
  visa_status?: string
  visa_expiry_date?: string
  zairyu_card_number?: string
  zairyu_card_expiry?: string
  passport_number?: string
  passport_expiry?: string
  has_employment_insurance?: boolean
  employment_insurance_number?: string
  has_health_insurance?: boolean
  health_insurance_number?: string
  has_pension_insurance?: boolean
  pension_insurance_number?: string
  has_workers_comp?: boolean
  yukyu_total?: number
  yukyu_used?: number
  yukyu_remaining?: number
  yukyu_grant_date?: string
  apartment_id?: number
  apartment_name?: string
  apartment_room?: string
  apartment_rent?: number
  is_corporate_housing?: boolean
  housing_subsidy?: number
  bank_name?: string
  bank_branch?: string
  bank_account_type?: string
  bank_account_number?: string
  bank_account_holder?: string
  qualifications?: string
  drivers_license?: string
  drivers_license_expiry?: string
  forklift_license?: boolean
  notes?: string
  photo_url?: string
}

export interface EmployeeUpdate {
  full_name_kanji?: string
  full_name_kana?: string
  full_name_romaji?: string
  gender?: string
  date_of_birth?: string
  age?: number
  nationality?: string
  postal_code?: string
  address?: string
  phone?: string
  mobile?: string
  email?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
  termination_date?: string
  termination_reason?: string
  status?: string
  contract_type?: string
  employment_type?: string
  factory_id?: number
  factory_line_id?: number
  company_name?: string
  plant_name?: string
  department?: string
  line_name?: string
  position?: string
  hourly_rate?: number
  billing_rate?: number
  transportation_allowance?: number
  visa_type?: string
  visa_status?: string
  visa_expiry_date?: string
  zairyu_card_number?: string
  zairyu_card_expiry?: string
  passport_number?: string
  passport_expiry?: string
  has_employment_insurance?: boolean
  employment_insurance_number?: string
  has_health_insurance?: boolean
  health_insurance_number?: string
  has_pension_insurance?: boolean
  pension_insurance_number?: string
  has_workers_comp?: boolean
  yukyu_total?: number
  yukyu_used?: number
  yukyu_remaining?: number
  yukyu_grant_date?: string
  apartment_id?: number
  apartment_name?: string
  apartment_room?: string
  apartment_rent?: number
  is_corporate_housing?: boolean
  housing_subsidy?: number
  bank_name?: string
  bank_branch?: string
  bank_account_type?: string
  bank_account_number?: string
  bank_account_holder?: string
  qualifications?: string
  drivers_license?: string
  drivers_license_expiry?: string
  forklift_license?: boolean
  notes?: string
  photo_url?: string
}

export interface EmployeeResponse {
  id: number
  employee_number: string
  hakenmoto_id?: string
  rirekisho_id?: string
  full_name_kanji: string
  full_name_kana: string
  full_name_romaji?: string
  gender?: string
  date_of_birth?: string
  nationality: string
  postal_code?: string
  address?: string
  phone?: string
  mobile?: string
  email?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
  hire_date: string
  termination_date?: string
  termination_reason?: string
  status: string
  contract_type?: string
  employment_type?: string
  factory_id?: number
  factory_line_id?: number
  company_name?: string
  plant_name?: string
  department?: string
  line_name?: string
  position?: string
  hourly_rate?: number
  billing_rate?: number
  transportation_allowance?: number
  visa_type?: string
  visa_expiry_date?: string
  zairyu_card_number?: string
  passport_number?: string
  has_employment_insurance: boolean
  has_health_insurance: boolean
  has_pension_insurance: boolean
  yukyu_total: number
  yukyu_used: number
  yukyu_remaining: number
  apartment_name?: string
  apartment_room?: string
  apartment_rent?: number
  is_corporate_housing: boolean
  bank_name?: string
  bank_branch?: string
  bank_account_type?: string
  bank_account_number?: string
  bank_account_holder?: string
  notes?: string
  age?: number
  display_name?: string  // 日本人→漢字, 外国人→カタカナ
  age_category?: string  // 年齢区分 for 派遣先通知書
  is_indefinite_employment: boolean
  employment_type_display: string
  created_at: string
  updated_at?: string
}

export interface EmployeeListItem {
  id: number
  employee_number: string
  full_name_kanji: string
  full_name_kana: string
  company_name?: string
  plant_name?: string
  department?: string
  line_name?: string
  hire_date: string
  hourly_rate?: number  // 時給 (lo que pagamos al empleado)
  billing_rate?: number  // 単価 (lo que la fábrica nos paga)
  status: string
  nationality: string
  visa_expiry_date?: string
  age?: number
}

export interface EmployeeForContract {
  id: number
  employee_number: string
  full_name_kanji: string
  full_name_kana: string
  display_name: string  // 日本人→漢字, 外国人→カタカナ
  gender?: string
  age?: number
  age_category: string  // 年齢区分 for 派遣先通知書
  nationality: string
  has_employment_insurance: boolean
  has_health_insurance: boolean
  has_pension_insurance: boolean
  is_indefinite_employment: boolean
}

export interface EmployeeStats {
  total_employees: number
  active_employees: number
  resigned_employees: number
  visa_expiring_soon: number
  average_age?: number
  under_18_count: number
  over_60_count: number
  by_company: { company_name: string; count: number }[]
  by_nationality: { nationality: string; count: number }[]
}

export interface EmployeeListParams {
  skip?: number
  limit?: number
  search?: string
  status?: string
  company_name?: string
  factory_id?: number
  nationality?: string
  visa_expiring_days?: number
}

// ========================================
// COMPANY SETTINGS TYPES (派遣元)
// ========================================

export interface CompanyInfo {
  name: string
  name_legal: string
  postal_code: string
  address: string
  full_address: string
  tel: string
  mobile: string
  fax?: string
  email: string
  website: string
}

export interface LicenseInfo {
  dispatch_license: string  // 労働者派遣事業
  support_org: string  // 登録支援機関
  job_placement: string  // 有料職業紹介事業
}

export interface ManagerInfo {
  name: string
  position: string
}

export interface CompanySettings {
  company: CompanyInfo
  licenses: LicenseInfo
  manager: ManagerInfo
}
