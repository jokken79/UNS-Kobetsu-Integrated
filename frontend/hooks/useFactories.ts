import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import {
  FactoryListItem,
  FactoryResponse,
  FactoryCreate,
  FactoryUpdate
} from '@/types';

/**
 * Hook to fetch all factories for the tree view
 */
export function useFactoryList() {
  return useQuery({
    queryKey: ['factories', 'list'],
    queryFn: async () => {
      const { data } = await api.get<FactoryListItem[]>('/factories');
      return data;
    },
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
}

/**
 * Hook to fetch a single factory with full details
 */
export function useFactory(factoryId: number | null) {
  return useQuery({
    queryKey: ['factories', factoryId],
    queryFn: async () => {
      if (!factoryId) return null;
      const { data } = await api.get<FactoryResponse>(`/factories/${factoryId}`);
      return data;
    },
    enabled: !!factoryId,
  });
}

/**
 * Hook to create a new factory
 */
export function useCreateFactory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: FactoryCreate) => {
      const { data: result } = await api.post<FactoryResponse>('/factories', data);
      return result;
    },
    onSuccess: () => {
      // Invalidate the factory list to refetch
      queryClient.invalidateQueries({ queryKey: ['factories', 'list'] });
    },
  });
}

/**
 * Hook to update a factory
 */
export function useUpdateFactory(factoryId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: FactoryUpdate) => {
      const { data: result } = await api.put<FactoryResponse>(`/factories/${factoryId}`, data);
      return result;
    },
    onSuccess: (data) => {
      // Update the specific factory cache
      queryClient.setQueryData(['factories', factoryId], data);
      // Invalidate the list to show updated data
      queryClient.invalidateQueries({ queryKey: ['factories', 'list'] });
    },
  });
}

/**
 * Hook to delete a factory
 */
export function useDeleteFactory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (factoryId: number) => {
      await api.delete(`/factories/${factoryId}`);
    },
    onSuccess: () => {
      // Invalidate the factory list
      queryClient.invalidateQueries({ queryKey: ['factories'] });
    },
  });
}

/**
 * Hook to get factories grouped by company (for dropdown selects)
 */
export function useFactoriesByCompany() {
  return useQuery({
    queryKey: ['factories', 'by-company'],
    queryFn: async () => {
      const { data } = await api.get<FactoryListItem[]>('/factories');

      // Group factories by company
      const grouped = new Map<string, FactoryListItem[]>();
      data.forEach((factory) => {
        const existing = grouped.get(factory.company_name) || [];
        grouped.set(factory.company_name, [...existing, factory]);
      });

      // Convert to array format
      const result = Array.from(grouped.entries()).map(([company, factories]) => ({
        company_name: company,
        factories: factories.sort((a, b) => a.plant_name.localeCompare(b.plant_name)),
      }));

      return result.sort((a, b) => a.company_name.localeCompare(b.company_name));
    },
    staleTime: 5 * 60 * 1000,
  });
}