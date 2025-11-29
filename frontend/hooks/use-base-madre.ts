/**
 * React Hooks para integración con Super Base Madre
 *
 * Estos hooks proporcionan una interfaz simple para consumir
 * datos de empleados, empresas y plantas desde Base Madre.
 */

import { useState, useEffect, useCallback } from 'react';
import { baseMadreClient, Employee, Company, Plant } from '@/lib/base-madre-client';

/**
 * Hook para obtener lista de empleados con filtros opcionales
 */
export function useEmployees(params?: {
  company_id?: number;
  status?: string;
  limit?: number;
  enabled?: boolean; // Control manual de cuando cargar
}) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0,
    has_more: false,
  });

  const enabled = params?.enabled !== undefined ? params.enabled : true;

  const fetchEmployees = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.getEmployees({
        company_id: params?.company_id,
        status: params?.status,
        limit: params?.limit || 100,
      });

      if (response.success) {
        setEmployees(response.data);
        setPagination(response.pagination);
      } else {
        setError('Failed to fetch employees');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch employees');
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  }, [params?.company_id, params?.status, params?.limit, enabled]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  return {
    employees,
    loading,
    error,
    pagination,
    refetch: fetchEmployees,
  };
}

/**
 * Hook para obtener un empleado específico por ID
 */
export function useEmployee(id: number | null, options?: { enabled?: boolean }) {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const enabled = options?.enabled !== undefined ? options.enabled : true;

  const fetchEmployee = useCallback(async () => {
    if (!id || !enabled) {
      setEmployee(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.getEmployee(id);

      if (response.success) {
        setEmployee(response.data);
      } else {
        setError('Employee not found');
        setEmployee(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch employee');
      setEmployee(null);
    } finally {
      setLoading(false);
    }
  }, [id, enabled]);

  useEffect(() => {
    fetchEmployee();
  }, [fetchEmployee]);

  return {
    employee,
    loading,
    error,
    refetch: fetchEmployee,
  };
}

/**
 * Hook para buscar empleados con debounce
 */
export function useEmployeeSearch(initialQuery = '', debounceMs = 300) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);
  const [results, setResults] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce the search query
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);

    return () => {
      clearTimeout(handler);
    };
  }, [query, debounceMs]);

  // Perform search when debounced query changes
  useEffect(() => {
    const searchEmployees = async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) {
        setResults([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await baseMadreClient.searchEmployees(debouncedQuery);

        if (response.success) {
          setResults(response.data);
        } else {
          setError('Search failed');
          setResults([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    searchEmployees();
  }, [debouncedQuery]);

  return {
    query,
    setQuery,
    results,
    loading,
    error,
    hasResults: results.length > 0,
  };
}

/**
 * Hook para obtener lista de empresas
 */
export function useCompanies(options?: { enabled?: boolean }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const enabled = options?.enabled !== undefined ? options.enabled : true;

  const fetchCompanies = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.getCompanies();

      if (response.success) {
        setCompanies(response.data);
      } else {
        setError('Failed to fetch companies');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch companies');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  return {
    companies,
    loading,
    error,
    refetch: fetchCompanies,
  };
}

/**
 * Hook para obtener detalles de una empresa específica
 */
export function useCompany(id: number | null, options?: { enabled?: boolean }) {
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const enabled = options?.enabled !== undefined ? options.enabled : true;

  const fetchCompany = useCallback(async () => {
    if (!id || !enabled) {
      setCompany(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.getCompany(id);

      if (response.success) {
        setCompany(response.data);
      } else {
        setError('Company not found');
        setCompany(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch company');
      setCompany(null);
    } finally {
      setLoading(false);
    }
  }, [id, enabled]);

  useEffect(() => {
    fetchCompany();
  }, [fetchCompany]);

  return {
    company,
    loading,
    error,
    refetch: fetchCompany,
  };
}

/**
 * Hook para obtener plantas, opcionalmente filtradas por empresa
 */
export function usePlants(companyId?: number, options?: { enabled?: boolean }) {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const enabled = options?.enabled !== undefined ? options.enabled : true;

  const fetchPlants = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.getPlants(companyId);

      if (response.success) {
        setPlants(response.data);
      } else {
        setError('Failed to fetch plants');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch plants');
      setPlants([]);
    } finally {
      setLoading(false);
    }
  }, [companyId, enabled]);

  useEffect(() => {
    fetchPlants();
  }, [fetchPlants]);

  return {
    plants,
    loading,
    error,
    refetch: fetchPlants,
  };
}

/**
 * Hook para verificar la conexión con Base Madre
 */
export function useBaseMadreHealth() {
  const [status, setStatus] = useState<'unknown' | 'healthy' | 'error'>('unknown');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await baseMadreClient.health();

      if (response.status === 'healthy') {
        setStatus('healthy');
      } else {
        setStatus('error');
        setError('Service unavailable');
      }
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Cannot connect to Base Madre');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return {
    status,
    loading,
    error,
    isHealthy: status === 'healthy',
    refetch: checkHealth,
  };
}
