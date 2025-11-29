'use client';

import { useState } from 'react';
import { useEmployees, useCompanies, usePlants, useBaseMadreHealth } from '@/hooks/use-base-madre';
import { EmployeeSelector } from '@/components/base-madre/EmployeeSelector';
import { EmployeeDetailsCard } from '@/components/base-madre/EmployeeDetailsCard';
import { Employee } from '@/lib/base-madre-client';

export default function BaseMadreTestPage() {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | undefined>(undefined);

  // Test health connection
  const { status: healthStatus, isHealthy, error: healthError } = useBaseMadreHealth();

  // Test employees
  const {
    employees,
    loading: employeesLoading,
    error: employeesError,
    pagination,
  } = useEmployees({
    company_id: selectedCompanyId,
    limit: 10,
  });

  // Test companies
  const { companies, loading: companiesLoading, error: companiesError } = useCompanies();

  // Test plants
  const { plants, loading: plantsLoading, error: plantsError } = usePlants(selectedCompanyId);

  const handleEmployeeSelect = (employeeId: number, employee: Employee) => {
    setSelectedEmployeeId(employeeId);
    // Employee selected for testing
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            🔗 Test de Integración - Super Base Madre
          </h1>
          <p className="text-gray-600 mt-2">
            Esta página te permite probar la integración con el sistema central de Base Madre
          </p>
        </div>

        {/* Health Status */}
        <div className="mb-8">
          <div
            className={`rounded-lg p-4 border-2 ${
              isHealthy
                ? 'bg-green-50 border-green-500'
                : healthStatus === 'unknown'
                ? 'bg-gray-50 border-gray-300'
                : 'bg-red-50 border-red-500'
            }`}
          >
            <div className="flex items-center gap-3">
              {isHealthy ? (
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : healthStatus === 'unknown' ? (
                <svg
                  className="animate-spin w-6 h-6 text-gray-600"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
              <div>
                <p className="font-semibold">
                  Estado de Conexión: {isHealthy ? '✅ Conectado' : healthStatus === 'unknown' ? '⏳ Verificando...' : '❌ Sin conexión'}
                </p>
                {healthError && <p className="text-sm text-red-600">{healthError}</p>}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Test 1: Employee Selector */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                1️⃣ Selector de Empleados
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Busca empleados por nombre, email o ID de empleado
              </p>
              <EmployeeSelector
                value={selectedEmployeeId}
                onChange={handleEmployeeSelect}
                companyId={selectedCompanyId}
                placeholder="Buscar empleado..."
              />
            </div>

            {/* Test 2: Companies */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                2️⃣ Empresas ({companies.length})
              </h2>
              {companiesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-gray-500 mt-2">Cargando empresas...</p>
                </div>
              ) : companiesError ? (
                <div className="text-red-600 text-sm">{companiesError}</div>
              ) : (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  <button
                    onClick={() => setSelectedCompanyId(undefined)}
                    className={`w-full text-left px-4 py-2 rounded-lg transition ${
                      selectedCompanyId === undefined
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <p className="font-medium">Todas las empresas</p>
                  </button>
                  {companies.map((company) => (
                    <button
                      key={company.id}
                      onClick={() => setSelectedCompanyId(company.id)}
                      className={`w-full text-left px-4 py-2 rounded-lg transition ${
                        selectedCompanyId === company.id
                          ? 'bg-blue-100 border-2 border-blue-500'
                          : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                      }`}
                    >
                      <p className="font-medium text-gray-900">{company.company_name}</p>
                      <p className="text-xs text-gray-500">
                        {company.employees_count} empleados • {company.plants_count} plantas
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Test 3: Recent Employees */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                3️⃣ Empleados Recientes
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                {selectedCompanyId
                  ? `Mostrando empleados de: ${companies.find((c) => c.id === selectedCompanyId)?.company_name}`
                  : 'Mostrando todos los empleados'}
              </p>
              {employeesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-gray-500 mt-2">Cargando empleados...</p>
                </div>
              ) : employeesError ? (
                <div className="text-red-600 text-sm">{employeesError}</div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {employees.map((employee) => (
                    <div
                      key={employee.id}
                      className="px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                          {employee.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{employee.name}</p>
                          <p className="text-xs text-gray-500">
                            {employee.employee_id} • {employee.company_name}
                          </p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            employee.status === '在職中'
                              ? 'bg-green-100 text-green-700'
                              : employee.status === '待機中'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {employee.status}
                        </span>
                      </div>
                    </div>
                  ))}
                  {pagination && (
                    <div className="mt-4 text-center text-sm text-gray-600">
                      Mostrando {employees.length} de {pagination.total} empleados
                      {pagination.has_more && ' (hay más disponibles)'}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Test 4: Employee Details */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                4️⃣ Detalles del Empleado
              </h2>
              {selectedEmployeeId ? (
                <EmployeeDetailsCard employeeId={selectedEmployeeId} />
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <svg
                    className="w-16 h-16 mx-auto text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                  <p className="mt-4">Selecciona un empleado para ver sus detalles</p>
                  <p className="text-sm">Usa el selector de arriba</p>
                </div>
              )}
            </div>

            {/* Test 5: Plants */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                5️⃣ Plantas ({plants.length})
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                {selectedCompanyId
                  ? `Plantas de: ${companies.find((c) => c.id === selectedCompanyId)?.company_name}`
                  : 'Todas las plantas'}
              </p>
              {plantsLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-gray-500 mt-2">Cargando plantas...</p>
                </div>
              ) : plantsError ? (
                <div className="text-red-600 text-sm">{plantsError}</div>
              ) : plants.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No hay plantas disponibles</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {plants.map((plant) => (
                    <div key={plant.id} className="px-4 py-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start gap-3">
                        <svg
                          className="w-5 h-5 text-gray-400 mt-0.5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                          />
                        </svg>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{plant.plant_name}</p>
                          <p className="text-xs text-gray-600">{plant.company_name}</p>
                          <div className="flex gap-4 mt-2 text-xs text-gray-500">
                            <span>👥 {plant.employees_count} empleados</span>
                            <span>⚙️ {plant.production_lines_count} líneas</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Configuration Info */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-bold text-blue-900 mb-2">📝 Configuración</h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>
              <strong>API URL:</strong> {process.env.NEXT_PUBLIC_BASE_MADRE_API_URL || process.env.BASE_MADRE_API_URL || 'http://localhost:5000/api/v1'}
            </p>
            <p>
              <strong>API Key:</strong> {process.env.NEXT_PUBLIC_BASE_MADRE_API_KEY || process.env.BASE_MADRE_API_KEY ? '✅ Configurada' : '❌ No configurada'}
            </p>
            <p className="text-xs mt-2 text-blue-600">
              💡 Configura las variables de entorno en <code>.env.local</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
