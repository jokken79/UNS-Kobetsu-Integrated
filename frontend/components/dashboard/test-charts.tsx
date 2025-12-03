// Test file to verify chart components work
// This can be removed after verification

import { ContractsByMonthChart } from './ContractsByMonthChart'
import { ContractsByStatusChart } from './ContractsByStatusChart'
import { EmployeesByFactoryChart } from './EmployeesByFactoryChart'

export function TestCharts() {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Chart Components Test</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Contracts by Month</h2>
          <div className="h-64">
            <ContractsByMonthChart className="h-full" />
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Contracts by Status</h2>
          <div className="h-64">
            <ContractsByStatusChart className="h-full" />
          </div>
        </div>

        <div className="border rounded-lg p-4 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Employees by Factory</h2>
          <div className="h-64">
            <EmployeesByFactoryChart className="h-full" />
          </div>
        </div>
      </div>
    </div>
  )
}