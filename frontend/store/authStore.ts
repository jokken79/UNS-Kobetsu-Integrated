/**
 * Auth Store using Zustand
 * Manages authentication state
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi } from '@/lib/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          await authApi.login({ email, password })
          const user = await authApi.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
          let errorMessage = 'ログインに失敗しました'

          if (error instanceof Error) {
            errorMessage = error.message
          } else if (
            typeof error === 'object' &&
            error !== null &&
            'response' in error &&
            typeof (error as { response?: { data?: { detail?: string } } }).response?.data?.detail === 'string'
          ) {
            errorMessage = (error as { response: { data: { detail: string } } }).response.data.detail
          }

          set({
            error: errorMessage,
            isLoading: false,
          })
          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true })
        try {
          await authApi.logout()
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
          // Redirect to login page after logout
          window.location.href = '/login'
        }
      },

      fetchUser: async () => {
        if (!authApi.isAuthenticated()) {
          set({ user: null, isAuthenticated: false })
          return
        }

        set({ isLoading: true })
        try {
          const user = await authApi.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
