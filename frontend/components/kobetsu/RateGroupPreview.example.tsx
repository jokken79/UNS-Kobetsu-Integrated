'use client'

import { useState } from 'react'
import { RateGroupPreview } from './RateGroupPreview'

/**
 * Example usage of RateGroupPreview component
 * This shows how to integrate the component with your contract creation flow
 */
export function RateGroupPreviewExample() {
  const [showPreview, setShowPreview] = useState(false)

  // Example data - this would come from your API
  const mockGroups = [
    {
      hourly_rate: 1650,
      billing_rate: 2100,
      employee_count: 2,
      employees: [
        {
          id: 1,
          employee_number: '1001',
          full_name_kanji: 'グエン・バン',
          full_name_kana: 'グエン・バン',
          department: '製造部',
          line_name: 'Aライン',
          hourly_rate: 1650,
          billing_rate: 2100
        },
        {
          id: 2,
          employee_number: '1045',
          full_name_kanji: 'レ・ティ',
          full_name_kana: 'レ・ティ',
          department: '製造部',
          line_name: 'Aライン',
          hourly_rate: 1650,
          billing_rate: 2100
        }
      ]
    },
    {
      hourly_rate: 1600,
      billing_rate: 2050,
      employee_count: 3,
      employees: [
        {
          id: 3,
          employee_number: '1089',
          full_name_kanji: 'ファン・ミン',
          full_name_kana: 'ファン・ミン',
          department: '製造部',
          line_name: 'Aライン',
          hourly_rate: 1600,
          billing_rate: 2050
        },
        {
          id: 4,
          employee_number: '1102',
          full_name_kanji: 'チャン・ホア',
          full_name_kana: 'チャン・ホア',
          department: '製造部',
          line_name: 'Aライン',
          hourly_rate: 1600,
          billing_rate: 2050
        },
        {
          id: 5,
          employee_number: '1115',
          full_name_kanji: 'ブイ・タン',
          full_name_kana: 'ブイ・タン',
          department: '製造部',
          line_name: 'Aライン',
          hourly_rate: 1600,
          billing_rate: 2050
        }
      ]
    }
  ]

  const handleConfirm = async (splitByRate: boolean) => {
    console.log('Creating contracts with split:', splitByRate)

    // Here you would call your API to create contracts
    // If splitByRate is true, create multiple contracts
    // If splitByRate is false, create a single contract

    if (splitByRate) {
      // Create one contract for each rate group
      for (const group of mockGroups) {
        console.log(`Creating contract for ${group.employee_count} employees at ¥${group.hourly_rate}`)
        // await createContract({ employees: group.employees, hourly_rate: group.hourly_rate })
      }
    } else {
      // Create a single contract with all employees
      const allEmployees = mockGroups.flatMap(g => g.employees)
      console.log(`Creating single contract for ${allEmployees.length} employees`)
      // await createContract({ employees: allEmployees })
    }

    setShowPreview(false)
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Rate Group Preview Example</h1>

      <button
        onClick={() => setShowPreview(true)}
        className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
      >
        Show Rate Group Preview
      </button>

      {showPreview && (
        <RateGroupPreview
          groups={mockGroups}
          totalEmployees={5}
          hasMultipleRates={true}
          suggestedContracts={2}
          message="5名を2つの契約に分割することを推奨します"
          onConfirm={handleConfirm}
          onCancel={() => setShowPreview(false)}
          isLoading={false}
        />
      )}
    </div>
  )
}

/**
 * Integration with KobetsuFormHybrid
 *
 * In your KobetsuFormHybrid component, you would:
 *
 * 1. After selecting employees and before creating contracts, check for rate differences
 * 2. If multiple rates detected, show the RateGroupPreview
 * 3. Based on user choice, create single or multiple contracts
 *
 * Example hook usage:
 *
 * const { mutate: createMultipleContracts } = useMutation({
 *   mutationFn: async (groups: RateGroup[]) => {
 *     const promises = groups.map(group =>
 *       api.post('/api/v1/kobetsu', {
 *         ...baseContractData,
 *         employee_ids: group.employees.map(e => e.id),
 *         hourly_rate: group.hourly_rate,
 *         billing_rate: group.billing_rate
 *       })
 *     )
 *     return Promise.all(promises)
 *   },
 *   onSuccess: (contracts) => {
 *     toast.success(`${contracts.length}件の契約を作成しました`)
 *     router.push('/kobetsu')
 *   }
 * })
 */