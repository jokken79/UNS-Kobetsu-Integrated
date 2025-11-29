/**
 * Tests for custom React hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the API module
vi.mock('@/lib/api', () => ({
  kobetsuApi: {
    getList: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getStats: vi.fn(),
  },
  factoryApi: {
    getList: vi.fn(),
    getCompanies: vi.fn(),
    getPlants: vi.fn(),
    getDepartments: vi.fn(),
    getLines: vi.fn(),
  },
  employeeApi: {
    getList: vi.fn(),
    getForContract: vi.fn(),
    getStats: vi.fn(),
  },
  syncApi: {
    getStatus: vi.fn(),
    syncEmployees: vi.fn(),
    syncFactories: vi.fn(),
    syncAll: vi.fn(),
  },
}))

// Import hooks after mocking
import { useBaseMadre } from '@/hooks/use-base-madre'
import { kobetsuApi, syncApi } from '@/lib/api'

// Create a wrapper component for React Query hooks
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  )
}

describe('useBaseMadre Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getSyncStatus', () => {
    it('should fetch sync status successfully', async () => {
      const mockStatus = {
        employees: { total: 100, active: 80, resigned: 20 },
        factories: { total: 10, lines: 25 },
      }

      vi.mocked(syncApi.getStatus).mockResolvedValueOnce(mockStatus)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      const status = await result.current.getSyncStatus()

      expect(syncApi.getStatus).toHaveBeenCalledTimes(1)
      expect(status).toEqual(mockStatus)
    })

    it('should handle sync status error', async () => {
      const mockError = new Error('Failed to fetch status')
      vi.mocked(syncApi.getStatus).mockRejectedValueOnce(mockError)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      await expect(result.current.getSyncStatus()).rejects.toThrow('Failed to fetch status')
    })
  })

  describe('syncEmployees', () => {
    it('should sync employees successfully', async () => {
      const mockResult = {
        employees: {
          total: 100,
          created: 10,
          updated: 5,
          errors: [],
        },
        elapsed_seconds: 2.5,
      }

      vi.mocked(syncApi.syncEmployees).mockResolvedValueOnce(mockResult)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      const syncResult = await result.current.syncEmployees()

      expect(syncApi.syncEmployees).toHaveBeenCalledTimes(1)
      expect(syncResult).toEqual(mockResult)
    })

    it('should handle sync employees error', async () => {
      const mockError = new Error('Sync failed')
      vi.mocked(syncApi.syncEmployees).mockRejectedValueOnce(mockError)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      await expect(result.current.syncEmployees()).rejects.toThrow('Sync failed')
    })
  })

  describe('syncFactories', () => {
    it('should sync factories successfully', async () => {
      const mockResult = {
        factories: {
          total: 50,
          created: 5,
          updated: 3,
          errors: [],
        },
        elapsed_seconds: 1.2,
      }

      vi.mocked(syncApi.syncFactories).mockResolvedValueOnce(mockResult)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      const syncResult = await result.current.syncFactories()

      expect(syncApi.syncFactories).toHaveBeenCalledTimes(1)
      expect(syncResult).toEqual(mockResult)
    })
  })

  describe('syncAll', () => {
    it('should sync all data successfully', async () => {
      const mockResult = {
        employees: {
          total: 100,
          created: 10,
          updated: 5,
          errors: [],
        },
        factories: {
          total: 50,
          created: 5,
          updated: 3,
          errors: [],
        },
        elapsed_seconds: 5.5,
      }

      vi.mocked(syncApi.syncAll).mockResolvedValueOnce(mockResult)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      const syncResult = await result.current.syncAll()

      expect(syncApi.syncAll).toHaveBeenCalledTimes(1)
      expect(syncResult).toEqual(mockResult)
      expect(syncResult.employees?.created).toBe(10)
      expect(syncResult.factories?.created).toBe(5)
    })

    it('should handle partial failures in syncAll', async () => {
      const mockResult = {
        employees: {
          total: 100,
          created: 10,
          updated: 5,
          errors: [
            { row: 15, message: 'Invalid employee data' },
            { row: 23, message: 'Duplicate employee number' },
          ],
        },
        factories: {
          total: 50,
          created: 5,
          updated: 3,
          errors: [],
        },
        elapsed_seconds: 5.5,
      }

      vi.mocked(syncApi.syncAll).mockResolvedValueOnce(mockResult)

      const { result } = renderHook(() => useBaseMadre(), {
        wrapper: createWrapper(),
      })

      const syncResult = await result.current.syncAll()

      expect(syncResult.employees?.errors).toHaveLength(2)
      expect(syncResult.factories?.errors).toHaveLength(0)
    })
  })
})

describe('Custom Hook Patterns', () => {
  describe('useKobetsuList (example)', () => {
    it('should fetch kobetsu list with filters', async () => {
      const mockData = {
        items: [
          {
            id: 1,
            contract_number: 'KOB-202411-0001',
            worksite_name: 'Test Factory',
            status: 'active',
          },
          {
            id: 2,
            contract_number: 'KOB-202411-0002',
            worksite_name: 'Sample Plant',
            status: 'draft',
          },
        ],
        total: 2,
        skip: 0,
        limit: 20,
      }

      vi.mocked(kobetsuApi.getList).mockResolvedValueOnce(mockData)

      // Simulate hook usage
      const useKobetsuList = (filters?: any) => {
        const [data, setData] = React.useState<typeof mockData | null>(null)
        const [isLoading, setIsLoading] = React.useState(true)
        const [error, setError] = React.useState<Error | null>(null)

        React.useEffect(() => {
          kobetsuApi.getList(filters)
            .then(setData)
            .catch(setError)
            .finally(() => setIsLoading(false))
        }, [])

        return { data, isLoading, error }
      }

      const { result } = renderHook(() => useKobetsuList({ status: 'active' }), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(kobetsuApi.getList).toHaveBeenCalledWith({ status: 'active' })
      expect(result.current.data).toEqual(mockData)
      expect(result.current.error).toBeNull()
    })
  })

  describe('useAuth (example)', () => {
    it('should manage authentication state', () => {
      // Simulate useAuth hook
      const useAuth = () => {
        const [isAuthenticated, setIsAuthenticated] = React.useState(false)
        const [user, setUser] = React.useState<{ id: number; username: string } | null>(null)

        const login = async (username: string, password: string) => {
          // Mock login implementation
          if (username === 'test@example.com' && password === 'password') {
            setIsAuthenticated(true)
            setUser({ id: 1, username })
            return { success: true }
          }
          throw new Error('Invalid credentials')
        }

        const logout = () => {
          setIsAuthenticated(false)
          setUser(null)
        }

        return { isAuthenticated, user, login, logout }
      }

      const { result } = renderHook(() => useAuth())

      // Initial state
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()

      // After login
      result.current.login('test@example.com', 'password').then(() => {
        expect(result.current.isAuthenticated).toBe(true)
        expect(result.current.user).toEqual({ id: 1, username: 'test@example.com' })
      })

      // After logout
      result.current.logout()
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })

  describe('useDebounce (utility hook)', () => {
    it('should debounce value changes', async () => {
      vi.useFakeTimers()

      const useDebounce = (value: string, delay: number) => {
        const [debouncedValue, setDebouncedValue] = React.useState(value)

        React.useEffect(() => {
          const timer = setTimeout(() => setDebouncedValue(value), delay)
          return () => clearTimeout(timer)
        }, [value, delay])

        return debouncedValue
      }

      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      expect(result.current).toBe('initial')

      // Change value
      rerender({ value: 'updated' })

      // Should still be initial before delay
      expect(result.current).toBe('initial')

      // Fast forward time
      vi.advanceTimersByTime(500)

      // Should now be updated
      await waitFor(() => {
        expect(result.current).toBe('updated')
      })

      vi.useRealTimers()
    })
  })

  describe('useLocalStorage (persistence hook)', () => {
    it('should persist value to localStorage', () => {
      const useLocalStorage = <T>(key: string, initialValue: T) => {
        const [value, setValue] = React.useState<T>(() => {
          try {
            const item = window.localStorage.getItem(key)
            return item ? JSON.parse(item) : initialValue
          } catch {
            return initialValue
          }
        })

        const setStoredValue = (newValue: T | ((prev: T) => T)) => {
          try {
            const valueToStore = newValue instanceof Function ? newValue(value) : newValue
            setValue(valueToStore)
            window.localStorage.setItem(key, JSON.stringify(valueToStore))
          } catch (error) {
            console.error(`Error saving to localStorage:`, error)
          }
        }

        return [value, setStoredValue] as const
      }

      const { result } = renderHook(() => useLocalStorage('testKey', 'defaultValue'))

      expect(result.current[0]).toBe('defaultValue')

      // Update value
      result.current[1]('newValue')

      expect(result.current[0]).toBe('newValue')
      expect(localStorage.getItem('testKey')).toBe('"newValue"')

      // Clear localStorage after test
      localStorage.removeItem('testKey')
    })
  })

  describe('usePagination (list management hook)', () => {
    it('should manage pagination state', () => {
      const usePagination = (totalItems: number, itemsPerPage = 20) => {
        const [currentPage, setCurrentPage] = React.useState(1)

        const totalPages = Math.ceil(totalItems / itemsPerPage)
        const skip = (currentPage - 1) * itemsPerPage

        const goToPage = (page: number) => {
          if (page >= 1 && page <= totalPages) {
            setCurrentPage(page)
          }
        }

        const nextPage = () => goToPage(currentPage + 1)
        const prevPage = () => goToPage(currentPage - 1)

        return {
          currentPage,
          totalPages,
          skip,
          limit: itemsPerPage,
          goToPage,
          nextPage,
          prevPage,
          hasNext: currentPage < totalPages,
          hasPrev: currentPage > 1,
        }
      }

      const { result } = renderHook(() => usePagination(100, 20))

      // Initial state
      expect(result.current.currentPage).toBe(1)
      expect(result.current.totalPages).toBe(5)
      expect(result.current.skip).toBe(0)
      expect(result.current.hasNext).toBe(true)
      expect(result.current.hasPrev).toBe(false)

      // Go to next page
      result.current.nextPage()
      expect(result.current.currentPage).toBe(2)
      expect(result.current.skip).toBe(20)
      expect(result.current.hasPrev).toBe(true)

      // Go to specific page
      result.current.goToPage(5)
      expect(result.current.currentPage).toBe(5)
      expect(result.current.skip).toBe(80)
      expect(result.current.hasNext).toBe(false)

      // Try to go beyond limits
      result.current.nextPage()
      expect(result.current.currentPage).toBe(5) // Should stay at 5

      result.current.goToPage(0)
      expect(result.current.currentPage).toBe(5) // Should stay at 5
    })
  })
})