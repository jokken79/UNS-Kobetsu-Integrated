/**
 * API Client for UNS Kobetsu Keiyakusho
 * Axios-based client with JWT authentication
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  KobetsuCreate,
  KobetsuUpdate,
  KobetsuResponse,
  KobetsuListItem,
  KobetsuStats,
  KobetsuListParams,
  PaginatedResponse,
  LoginRequest,
  TokenResponse,
  User,
  FactoryCreate,
  FactoryUpdate,
  FactoryResponse,
  FactoryListItem,
  CompanyOption,
  PlantOption,
  DepartmentOption,
  LineOption,
  FactoryCascadeData,
  EmployeeCreate,
  EmployeeUpdate,
  EmployeeResponse,
  EmployeeListItem,
  EmployeeForContract,
  EmployeeStats,
  EmployeeListParams,
} from '@/types'

// Use relative path for API calls - Next.js rewrites proxy them to the backend
// This works regardless of how the user accesses the frontend (localhost, IP, domain)
const API_URL = '/api/v1'

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
        if (refreshToken) {
          const response = await axios.post<TokenResponse>(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token, refresh_token } = response.data
          localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
          localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }

          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', data)
    const { access_token, refresh_token } = response.data
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
    return response.data
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY)
  },
}

// Kobetsu Keiyakusho API
export const kobetsuApi = {
  // List contracts with pagination and filters
  getList: async (params?: KobetsuListParams): Promise<PaginatedResponse<KobetsuListItem>> => {
    const response = await apiClient.get<PaginatedResponse<KobetsuListItem>>('/kobetsu', {
      params,
    })
    return response.data
  },

  // Get single contract by ID
  getById: async (id: number): Promise<KobetsuResponse> => {
    const response = await apiClient.get<KobetsuResponse>(`/kobetsu/${id}`)
    return response.data
  },

  // Get contract by contract number
  getByNumber: async (contractNumber: string): Promise<KobetsuResponse> => {
    const response = await apiClient.get<KobetsuResponse>(`/kobetsu/by-number/${contractNumber}`)
    return response.data
  },

  // Create new contract
  create: async (data: KobetsuCreate): Promise<KobetsuResponse> => {
    const response = await apiClient.post<KobetsuResponse>('/kobetsu', data)
    return response.data
  },

  // Update contract
  update: async (id: number, data: KobetsuUpdate): Promise<KobetsuResponse> => {
    const response = await apiClient.put<KobetsuResponse>(`/kobetsu/${id}`, data)
    return response.data
  },

  // Delete contract
  delete: async (id: number, hard = false): Promise<void> => {
    await apiClient.delete(`/kobetsu/${id}`, { params: { hard } })
  },

  // Get statistics
  getStats: async (factoryId?: number): Promise<KobetsuStats> => {
    const response = await apiClient.get<KobetsuStats>('/kobetsu/stats', {
      params: { factory_id: factoryId },
    })
    return response.data
  },

  // Get expiring contracts
  getExpiring: async (days = 30): Promise<KobetsuListItem[]> => {
    const response = await apiClient.get<KobetsuListItem[]>('/kobetsu/expiring', {
      params: { days },
    })
    return response.data
  },

  // Get contracts by factory
  getByFactory: async (factoryId: number): Promise<KobetsuListItem[]> => {
    const response = await apiClient.get<KobetsuListItem[]>(`/kobetsu/by-factory/${factoryId}`)
    return response.data
  },

  // Get contracts by employee
  getByEmployee: async (employeeId: number): Promise<KobetsuListItem[]> => {
    const response = await apiClient.get<KobetsuListItem[]>(`/kobetsu/by-employee/${employeeId}`)
    return response.data
  },

  // Activate draft contract
  activate: async (id: number): Promise<KobetsuResponse> => {
    const response = await apiClient.post<KobetsuResponse>(`/kobetsu/${id}/activate`)
    return response.data
  },

  // Renew contract
  renew: async (id: number, newEndDate: string): Promise<KobetsuResponse> => {
    const response = await apiClient.post<KobetsuResponse>(`/kobetsu/${id}/renew`, null, {
      params: { new_end_date: newEndDate },
    })
    return response.data
  },

  // Duplicate contract
  duplicate: async (id: number): Promise<KobetsuResponse> => {
    const response = await apiClient.post<KobetsuResponse>(`/kobetsu/${id}/duplicate`)
    return response.data
  },

  // Get employees for contract
  getEmployees: async (id: number): Promise<number[]> => {
    const response = await apiClient.get<number[]>(`/kobetsu/${id}/employees`)
    return response.data
  },

  // Add employee to contract
  addEmployee: async (id: number, employeeId: number): Promise<void> => {
    await apiClient.post(`/kobetsu/${id}/employees/${employeeId}`)
  },

  // Remove employee from contract
  removeEmployee: async (id: number, employeeId: number): Promise<void> => {
    await apiClient.delete(`/kobetsu/${id}/employees/${employeeId}`)
  },

  // Generate PDF/DOCX
  generatePDF: async (id: number, format: 'pdf' | 'docx' = 'pdf'): Promise<Blob> => {
    const response = await apiClient.post(`/kobetsu/${id}/generate-pdf`, null, {
      params: { format },
      responseType: 'blob',
    })
    return response.data
  },

  // Sign contract
  sign: async (id: number, pdfPath: string): Promise<{ message: string; signed_date: string; pdf_path: string }> => {
    const response = await apiClient.post(`/kobetsu/${id}/sign`, null, {
      params: { pdf_path: pdfPath },
    })
    return response.data
  },

  // Download signed PDF
  download: async (id: number): Promise<Blob> => {
    const response = await apiClient.get(`/kobetsu/${id}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Export to CSV
  exportCSV: async (status?: string, factoryId?: number): Promise<Blob> => {
    const response = await apiClient.get('/kobetsu/export/csv', {
      params: { status, factory_id: factoryId },
      responseType: 'blob',
    })
    return response.data
  },

  // ========================================
  // Smart Assignment API - 配属推奨システム
  // ========================================

  // Get assignment suggestion (add to existing vs create new)
  suggestAssignment: async (params: {
    employee_id: number
    factory_id: number
    factory_line_id: number
    start_date: string
  }): Promise<{
    recommendation: 'add_to_existing' | 'create_new'
    reason: string
    employee_id: number
    employee_name: string
    employee_rate: number | null
    existing_contract: {
      id: number
      contract_number: string
      worksite_name: string
      dispatch_start_date: string
      dispatch_end_date: string
      current_workers: number
      hourly_rate: number
    } | null
    rate_difference_pct: number | null
    conflict_date_info: {
      conflict_date: string | null
      days_remaining: number | null
      warning_level: string
      message: string
    }
  }> => {
    const response = await apiClient.get('/kobetsu/suggest/assignment', { params })
    return response.data
  },

  // Execute employee assignment
  assignEmployee: async (params: {
    employee_id: number
    factory_id: number
    factory_line_id: number
    start_date: string
    action: 'add_to_existing' | 'create_new'
    existing_contract_id?: number
    duration_months?: number
    hourly_rate?: number
  }): Promise<{
    action: string
    contract_id: number
    contract_number?: string
    employee_id: number
    message: string
    warnings?: string[]
  }> => {
    const response = await apiClient.post('/kobetsu/assign-employee', null, { params })
    return response.data
  },

  // Get employee details with effective rates for a contract
  getEmployeeDetails: async (contractId: number): Promise<{
    contract_id: number
    contract_rate: number
    employees: {
      employee_id: number
      employee_name: string
      effective_rate: number
      rate_source: string
      individual_start: string | null
      individual_end: string | null
    }[]
  }> => {
    const response = await apiClient.get(`/kobetsu/${contractId}/employees/details`)
    return response.data
  },

  // Validate dates against conflict date
  validateConflictDate: async (params: {
    factory_id: number
    proposed_end_date: string
  }): Promise<{
    valid: boolean
    conflict_date: string | null
    proposed_date: string
    days_before_conflict: number | null
    message: string
  }> => {
    const response = await apiClient.get('/kobetsu/validate/conflict-date', { params })
    return response.data
  },

  // Get suggested dates respecting conflict date
  suggestDates: async (params: {
    factory_id: number
    start_date: string
    duration_months?: number
  }): Promise<{
    suggested_start: string
    suggested_end: string
    conflict_date: string | null
    original_end: string
    was_adjusted: boolean
    message: string
  }> => {
    const response = await apiClient.get('/kobetsu/suggest/dates', { params })
    return response.data
  },

  // Get alerts for expiring contracts
  getExpiringContractsAlerts: async (days?: number): Promise<{
    id: number
    contract_number: string
    worksite_name: string
    dispatch_end_date: string
    days_remaining: number
    status: string
    employee_count: number
  }[]> => {
    const response = await apiClient.get('/kobetsu/alerts/expiring-contracts', {
      params: { days },
    })
    return response.data
  },

  // Get alerts for factories near conflict date
  getConflictDateAlerts: async (days?: number): Promise<{
    factory_id: number
    company_name: string
    plant_name: string
    conflict_date: string
    days_remaining: number
    active_contracts: number
    total_employees: number
  }[]> => {
    const response = await apiClient.get('/kobetsu/alerts/conflict-dates', {
      params: { days },
    })
    return response.data
  },

  // Validate employee compatibility for contract
  validateEmployeeCompatibility: async (params: {
    employee_ids: number[]
    factory_line_id: number
    hourly_rate: number
  }): Promise<{
    is_valid: boolean
    compatible_count: number
    incompatible_count: number
    compatible: Array<{
      id: number
      employee_number: string
      full_name_kanji: string
      line_name: string
      status: string
    }>
    incompatible: Array<{
      id: number
      employee_number: string
      full_name_kanji: string
      line_name: string
      issues: Array<{
        type: string
        reason: string
        severity: string
      }>
    }>
    suggestions: string[]
    summary: string
  }> => {
    const queryParams = new URLSearchParams()
    params.employee_ids.forEach(id => queryParams.append('employee_ids', id.toString()))
    queryParams.append('factory_line_id', params.factory_line_id.toString())
    queryParams.append('hourly_rate', params.hourly_rate.toString())

    const response = await apiClient.get(
      `/kobetsu/validate/employee-compatibility?${queryParams.toString()}`
    )
    return response.data
  },
}

// Factory API
export const factoryApi = {
  // List factories
  getList: async (params?: {
    skip?: number
    limit?: number
    search?: string
    company_name?: string
    is_active?: boolean
  }): Promise<FactoryListItem[]> => {
    const response = await apiClient.get<FactoryListItem[]>('/factories', { params })
    return response.data
  },

  // Get factory by ID
  getById: async (id: number): Promise<FactoryResponse> => {
    const response = await apiClient.get<FactoryResponse>(`/factories/${id}`)
    return response.data
  },

  // Create factory
  create: async (data: FactoryCreate): Promise<FactoryResponse> => {
    const response = await apiClient.post<FactoryResponse>('/factories', data)
    return response.data
  },

  // Update factory
  update: async (id: number, data: FactoryUpdate): Promise<FactoryResponse> => {
    const response = await apiClient.put<FactoryResponse>(`/factories/${id}`, data)
    return response.data
  },

  // Delete factory
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/factories/${id}`)
  },

  // Cascade dropdowns
  getCompanies: async (search?: string): Promise<CompanyOption[]> => {
    const response = await apiClient.get<CompanyOption[]>('/factories/dropdown/companies', {
      params: { search },
    })
    return response.data
  },

  getPlants: async (companyName: string): Promise<PlantOption[]> => {
    const response = await apiClient.get<PlantOption[]>('/factories/dropdown/plants', {
      params: { company_name: companyName },
    })
    return response.data
  },

  getDepartments: async (factoryId: number): Promise<DepartmentOption[]> => {
    const response = await apiClient.get<DepartmentOption[]>('/factories/dropdown/departments', {
      params: { factory_id: factoryId },
    })
    return response.data
  },

  getLines: async (factoryId: number, department?: string): Promise<LineOption[]> => {
    const response = await apiClient.get<LineOption[]>('/factories/dropdown/lines', {
      params: { factory_id: factoryId, department },
    })
    return response.data
  },

  // Get cascade data for selected line
  getCascadeData: async (lineId: number): Promise<FactoryCascadeData> => {
    const response = await apiClient.get<FactoryCascadeData>(`/factories/dropdown/cascade/${lineId}`)
    return response.data
  },
}

// Employee API
export const employeeApi = {
  // List employees
  getList: async (params?: EmployeeListParams): Promise<EmployeeListItem[]> => {
    const response = await apiClient.get<EmployeeListItem[]>('/employees', { params })
    return response.data
  },

  // Get employee by ID
  getById: async (id: number): Promise<EmployeeResponse> => {
    const response = await apiClient.get<EmployeeResponse>(`/employees/${id}`)
    return response.data
  },

  // Create employee
  create: async (data: EmployeeCreate): Promise<EmployeeResponse> => {
    const response = await apiClient.post<EmployeeResponse>('/employees', data)
    return response.data
  },

  // Update employee
  update: async (id: number, data: EmployeeUpdate): Promise<EmployeeResponse> => {
    const response = await apiClient.put<EmployeeResponse>(`/employees/${id}`, data)
    return response.data
  },

  // Delete employee
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/employees/${id}`)
  },

  // Get employees for contract selection
  getForContract: async (params?: {
    factory_id?: number
    search?: string
    exclude_ids?: string
    limit?: number
  }): Promise<EmployeeForContract[]> => {
    const response = await apiClient.get<EmployeeForContract[]>('/employees/for-contract', {
      params,
    })
    return response.data
  },

  // Get statistics
  getStats: async (): Promise<EmployeeStats> => {
    const response = await apiClient.get<EmployeeStats>('/employees/stats')
    return response.data
  },

  // Get employees with expiring visas
  getExpiringVisas: async (days = 30): Promise<EmployeeListItem[]> => {
    const response = await apiClient.get<EmployeeListItem[]>('/employees/visa/expiring', {
      params: { days },
    })
    return response.data
  },
}

// ========================================
// IMPORT API - データインポート
// ========================================

export interface ImportResponse {
  success: boolean
  total_rows: number
  imported_count: number
  updated_count: number
  skipped_count: number
  errors: { row: number; field: string; message: string; value?: string }[]
  preview_data: {
    row: number
    is_valid: boolean
    errors: string[]
    [key: string]: unknown
  }[]
  message: string
}

export const importApi = {
  // Preview factory import
  previewFactories: async (file: File): Promise<ImportResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<ImportResponse>('/import/factories/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // Execute factory import
  executeFactoryImport: async (
    previewData: unknown[],
    mode: 'create' | 'update' | 'sync' = 'create'
  ): Promise<ImportResponse> => {
    const response = await apiClient.post<ImportResponse>('/import/factories/execute', {
      preview_data: previewData,
      mode,
    })
    return response.data
  },

  // Preview employee import
  previewEmployees: async (file: File): Promise<ImportResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<ImportResponse>('/import/employees/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // Execute employee import
  executeEmployeeImport: async (
    previewData: unknown[],
    mode: 'create' | 'update' | 'sync' = 'sync'
  ): Promise<ImportResponse> => {
    const response = await apiClient.post<ImportResponse>('/import/employees/execute', {
      preview_data: previewData,
      mode,
    })
    return response.data
  },

  // One-click sync employees
  syncEmployees: async (file: File): Promise<ImportResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<ImportResponse>('/import/employees/sync', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // Download templates
  downloadFactoryTemplate: (format: 'excel' | 'json' = 'excel'): string => {
    return `${API_URL}/import/templates/factories?format=${format}`
  },

  downloadEmployeeTemplate: (): string => {
    return `${API_URL}/import/templates/employees`
  },
}

// ========================================
// SYNC API - データ同期
// ========================================

export interface SyncStatus {
  employees?: {
    total: number
    active: number
    resigned: number
  }
  factories?: {
    total: number
    lines: number
  }
}

export interface SyncResult {
  employees?: {
    total: number
    created: number
    updated: number
    errors: { row: number; message: string }[]
  }
  factories?: {
    total: number
    created: number
    updated: number
    errors: { row: number; message: string }[]
  }
  elapsed_seconds?: number
}

export const syncApi = {
  // Get current sync status
  getStatus: async (): Promise<SyncStatus> => {
    const response = await apiClient.get<SyncStatus>('/sync/status')
    return response.data
  },

  // Sync employees from master file
  syncEmployees: async (): Promise<SyncResult> => {
    const response = await apiClient.post<SyncResult>('/sync/employees')
    return response.data
  },

  // Sync factories from master file
  syncFactories: async (): Promise<SyncResult> => {
    const response = await apiClient.post<SyncResult>('/sync/factories')
    return response.data
  },

  // Sync all data
  syncAll: async (): Promise<SyncResult> => {
    const response = await apiClient.post<SyncResult>('/sync/all')
    return response.data
  },
}

// ========================================
// SETTINGS API (設定)
// ========================================

import type { CompanySettings } from '@/types'

// Types for form defaults
export interface ContactInfoEditable {
  department: string
  position: string
  name: string
  phone: string
}

export interface ManagerInfoEditable extends ContactInfoEditable {
  license_number?: string
}

export interface DefaultWorkConditions {
  work_days: string[]
  work_start_time: string
  work_end_time: string
  break_time_minutes: number
  hourly_rate: number
  overtime_rate: number
  responsibility_level: string
}

export interface UNSFormDefaults {
  complaint_contact: ContactInfoEditable
  manager: ManagerInfoEditable
  work_conditions: DefaultWorkConditions
}

export const settingsApi = {
  // Get company (派遣元) information
  getCompany: async (): Promise<CompanySettings> => {
    const response = await apiClient.get<CompanySettings>('/settings/company')
    return response.data
  },

  // Get system info
  getSystem: async (): Promise<{ app_name: string; version: string; environment: string }> => {
    const response = await apiClient.get('/settings/system')
    return response.data
  },

  // Get form defaults (派遣元連絡先・責任者・就業条件)
  getFormDefaults: async (): Promise<UNSFormDefaults> => {
    const response = await apiClient.get<UNSFormDefaults>('/settings/form-defaults')
    return response.data
  },

  // Update form defaults
  updateFormDefaults: async (defaults: UNSFormDefaults): Promise<UNSFormDefaults> => {
    const response = await apiClient.put<UNSFormDefaults>('/settings/form-defaults', defaults)
    return response.data
  },
}

export default apiClient
