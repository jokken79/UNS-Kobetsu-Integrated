/**
 * Tests for API client
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

// Mock axios BEFORE imports that use it
const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
}

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// Now import the modules that depend on axios
import axios from 'axios'
import { authApi, kobetsuApi } from '@/lib/api'

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Authentication API', () => {
    describe('login', () => {
      it('should store tokens on successful login', async () => {
        const mockResponse = {
          data: {
            access_token: 'test-access-token',
            refresh_token: 'test-refresh-token',
            token_type: 'bearer',
            expires_in: 3600,
          },
        }

        mockAxiosInstance.post.mockResolvedValueOnce(mockResponse)

        const result = await authApi.login({
          email: 'test@example.com',
          password: 'password123',
        })

        expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
          email: 'test@example.com',
          password: 'password123',
        })

        expect(localStorage.getItem('access_token')).toBe('test-access-token')
        expect(localStorage.getItem('refresh_token')).toBe('test-refresh-token')
        expect(result).toEqual(mockResponse.data)
      })

      it('should handle login failure', async () => {
        const mockError = new Error('Invalid credentials')
        mockAxiosInstance.post.mockRejectedValueOnce(mockError)

        await expect(
          authApi.login({
            email: 'invalid@example.com',
            password: 'wrong',
          })
        ).rejects.toThrow('Invalid credentials')

        expect(localStorage.getItem('access_token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
      })
    })

    describe('logout', () => {
      it('should clear tokens and call logout endpoint', async () => {
        localStorage.setItem('access_token', 'token-to-remove')
        localStorage.setItem('refresh_token', 'refresh-to-remove')

        mockAxiosInstance.post.mockResolvedValueOnce({ data: {} })

        await authApi.logout()

        expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/logout')
        expect(localStorage.getItem('access_token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
      })

      it('should still clear tokens even if logout endpoint fails', async () => {
        localStorage.setItem('access_token', 'token-to-remove')
        localStorage.setItem('refresh_token', 'refresh-to-remove')

        mockAxiosInstance.post.mockRejectedValueOnce(new Error('Network error'))

        await authApi.logout()

        expect(localStorage.getItem('access_token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
      })
    })

    describe('isAuthenticated', () => {
      it('should return true when access token exists', () => {
        localStorage.setItem('access_token', 'valid-token')
        expect(authApi.isAuthenticated()).toBe(true)
      })

      it('should return false when no access token', () => {
        localStorage.removeItem('access_token')
        expect(authApi.isAuthenticated()).toBe(false)
      })
    })

    describe('getCurrentUser', () => {
      it('should fetch current user data', async () => {
        const mockUser = {
          id: 1,
          username: 'test@example.com',
          full_name: 'Test User',
          is_active: true,
          is_superuser: false,
        }

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockUser })

        const result = await authApi.getCurrentUser()

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/me')
        expect(result).toEqual(mockUser)
      })
    })
  })

  describe('Kobetsu API', () => {
    describe('getList', () => {
      it('should fetch contracts with pagination params', async () => {
        const mockResponse = {
          data: {
            items: [
              { id: 1, contract_number: 'KOB-202411-0001', status: 'active' },
              { id: 2, contract_number: 'KOB-202411-0002', status: 'draft' },
            ],
            total: 2,
            skip: 0,
            limit: 20,
          },
        }

        mockAxiosInstance.get.mockResolvedValueOnce(mockResponse)

        const params = {
          skip: 0,
          limit: 20,
          status: 'active',
          factory_id: 1,
          search: 'test',
        }

        const result = await kobetsuApi.getList(params)

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/kobetsu', { params })
        expect(result).toEqual(mockResponse.data)
      })

      it('should handle empty results', async () => {
        const mockResponse = {
          data: {
            items: [],
            total: 0,
            skip: 0,
            limit: 20,
          },
        }

        mockAxiosInstance.get.mockResolvedValueOnce(mockResponse)

        const result = await kobetsuApi.getList()

        expect(result.items).toHaveLength(0)
        expect(result.total).toBe(0)
      })
    })

    describe('create', () => {
      it('should create a new contract with all required fields', async () => {
        const createData = {
          factory_id: 1,
          employee_ids: [1, 2, 3],
          contract_date: '2024-11-25',
          dispatch_start_date: '2024-12-01',
          dispatch_end_date: '2025-11-30',
          work_content: '製造ライン作業',
          responsibility_level: '通常業務',
          worksite_name: 'テスト工場',
          worksite_address: '東京都千代田区',
          supervisor_department: '製造部',
          supervisor_position: '課長',
          supervisor_name: '田中太郎',
          work_days: ['月', '火', '水', '木', '金'],
          work_start_time: '08:00',
          work_end_time: '17:00',
          break_time_minutes: 60,
          hourly_rate: 1500,
          overtime_rate: 1875,
          haken_moto_complaint_contact: {
            department: '人事部',
            position: '課長',
            name: '山田花子',
            phone: '03-1234-5678',
          },
          haken_saki_complaint_contact: {
            department: '総務部',
            position: '係長',
            name: '佐藤次郎',
            phone: '03-9876-5432',
          },
          haken_moto_manager: {
            department: '派遣事業部',
            position: '部長',
            name: '鈴木一郎',
            phone: '03-1234-5678',
          },
          haken_saki_manager: {
            department: '人事部',
            position: '部長',
            name: '高橋三郎',
            phone: '03-9876-5432',
          },
        }

        const mockResponse = {
          data: {
            id: 1,
            contract_number: 'KOB-202411-0001',
            ...createData,
            status: 'draft',
            created_at: '2024-11-25T10:00:00Z',
          },
        }

        mockAxiosInstance.post.mockResolvedValueOnce(mockResponse)

        const result = await kobetsuApi.create(createData)

        expect(mockAxiosInstance.post).toHaveBeenCalledWith('/kobetsu', createData)
        expect(result.contract_number).toBe('KOB-202411-0001')
        expect(result.status).toBe('draft')
      })

      it('should handle validation errors', async () => {
        const invalidData = {
          factory_id: 1,
          // Missing required fields
        }

        const mockError = {
          response: {
            status: 400,
            data: {
              detail: 'Validation error: work_content is required',
            },
          },
        }

        mockAxiosInstance.post.mockRejectedValueOnce(mockError)

        await expect(kobetsuApi.create(invalidData as any)).rejects.toMatchObject(mockError)
      })
    })

    describe('getStats', () => {
      it('should fetch statistics', async () => {
        const mockStats = {
          total_contracts: 50,
          active_contracts: 30,
          expired_contracts: 10,
          draft_contracts: 5,
          expiring_soon: 3,
          total_workers: 150,
        }

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockStats })

        const result = await kobetsuApi.getStats()

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/kobetsu/stats', {
          params: { factory_id: undefined },
        })
        expect(result).toEqual(mockStats)
      })

      it('should fetch statistics for specific factory', async () => {
        const mockStats = {
          total_contracts: 5,
          active_contracts: 3,
          expired_contracts: 1,
          draft_contracts: 1,
          expiring_soon: 0,
          total_workers: 15,
        }

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockStats })

        const result = await kobetsuApi.getStats(1)

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/kobetsu/stats', {
          params: { factory_id: 1 },
        })
        expect(result.total_contracts).toBe(5)
      })
    })

    describe('generatePDF', () => {
      it('should generate PDF document', async () => {
        const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' })
        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockBlob })

        const result = await kobetsuApi.generatePDF(1, 'pdf')

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/kobetsu/1/generate-pdf',
          null,
          {
            params: { format: 'pdf' },
            responseType: 'blob',
          }
        )
        expect(result).toBeInstanceOf(Blob)
      })

      it('should generate DOCX document', async () => {
        const mockBlob = new Blob(['docx content'], {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        })
        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockBlob })

        const result = await kobetsuApi.generatePDF(1, 'docx')

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/kobetsu/1/generate-pdf',
          null,
          {
            params: { format: 'docx' },
            responseType: 'blob',
          }
        )
        expect(result).toBeInstanceOf(Blob)
      })
    })
  })

  describe('Request Interceptors', () => {
    it('should add authorization header when token exists', () => {
      // Get the request interceptor
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0]

      localStorage.setItem('access_token', 'test-token')

      const config = {
        headers: {},
        url: '/test',
      }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('should not add authorization header when no token', () => {
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0]

      localStorage.removeItem('access_token')

      const config = {
        headers: {},
        url: '/test',
      }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Response Interceptors', () => {
    it('should handle 401 error and attempt token refresh', async () => {
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      localStorage.setItem('refresh_token', 'old-refresh-token')

      const originalRequest = {
        headers: {},
        url: '/protected',
        _retry: false,
      }

      const error = {
        response: { status: 401 },
        config: originalRequest,
      }

      // Mock the token refresh request
      vi.mocked(axios.post).mockResolvedValueOnce({
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
        },
      })

      // Mock the retry of the original request
      mockAxiosInstance.get.mockResolvedValueOnce({ data: 'success' })

      const result = await responseInterceptor(error)

      expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refresh_token: 'old-refresh-token',
      })

      expect(localStorage.getItem('access_token')).toBe('new-access-token')
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
      expect(originalRequest._retry).toBe(true)
    })

    it('should redirect to login when refresh fails', async () => {
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      // Mock window.location
      delete (window as any).location
      window.location = { href: '' } as any

      localStorage.setItem('refresh_token', 'expired-refresh-token')

      const originalRequest = {
        headers: {},
        url: '/protected',
        _retry: false,
      }

      const error = {
        response: { status: 401 },
        config: originalRequest,
      }

      // Mock failed token refresh
      vi.mocked(axios.post).mockRejectedValueOnce(new Error('Refresh failed'))

      await responseInterceptor(error)

      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(window.location.href).toBe('/login')
    })

    it('should pass through non-401 errors', async () => {
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const error = {
        response: { status: 500, data: { detail: 'Server error' } },
        config: {},
      }

      await expect(responseInterceptor(error)).rejects.toEqual(error)
    })
  })
})