'use client';

import { useState } from 'react';
import { FactoryTree } from './FactoryTree';
import { FactoryListItem } from '@/types';

// Example mock data
const mockFactories: FactoryListItem[] = [
  {
    id: 1,
    factory_id: 'FAC-001',
    company_name: '高雄工業',
    plant_name: '岡山工場',
    is_active: true,
    lines_count: 3,
    employees_count: 45,
  },
  {
    id: 2,
    factory_id: 'FAC-002',
    company_name: '高雄工業',
    plant_name: '本社工場',
    is_active: true,
    lines_count: 5,
    employees_count: 78,
  },
  {
    id: 3,
    factory_id: 'FAC-003',
    company_name: '高雄工業',
    plant_name: '海南第一',
    is_active: false,
    lines_count: 2,
    employees_count: 23,
  },
  {
    id: 4,
    factory_id: 'FAC-004',
    company_name: '高雄工業',
    plant_name: '海南第二',
    is_active: true,
    lines_count: 4,
    employees_count: 56,
  },
  {
    id: 5,
    factory_id: 'FAC-005',
    company_name: '高雄工業',
    plant_name: '名古屋工場',
    is_active: true,
    lines_count: 6,
    employees_count: 92,
  },
  {
    id: 6,
    factory_id: 'FAC-006',
    company_name: 'コーリツ',
    plant_name: '本社工場',
    is_active: true,
    lines_count: 3,
    employees_count: 34,
  },
  {
    id: 7,
    factory_id: 'FAC-007',
    company_name: 'コーリツ',
    plant_name: '豊田工場',
    is_active: true,
    lines_count: 4,
    employees_count: 45,
  },
  {
    id: 8,
    factory_id: 'FAC-008',
    company_name: 'コーリツ',
    plant_name: '刈谷工場',
    is_active: true,
    lines_count: 2,
    employees_count: 28,
  },
  {
    id: 9,
    factory_id: 'FAC-009',
    company_name: 'コーリツ',
    plant_name: '安城工場',
    is_active: false,
    lines_count: 1,
    employees_count: 12,
  },
  {
    id: 10,
    factory_id: 'FAC-010',
    company_name: '美鈴工業',
    plant_name: '本社工場',
    is_active: true,
    lines_count: 5,
    employees_count: 67,
  },
];

/**
 * Example page showing split view with FactoryTree on the left
 */
export function FactoryTreeExample() {
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(1);
  const [isLoading, setIsLoading] = useState(false);

  const handleCreateNew = () => {
    console.log('Create new factory clicked');
    // In a real app, this would open a modal or navigate to create page
  };

  const handleSelectFactory = (factoryId: number) => {
    console.log('Selected factory:', factoryId);
    setSelectedFactoryId(factoryId);
    // In a real app, this would load factory details in the right panel
  };

  // Find selected factory for details display
  const selectedFactory = mockFactories.find((f) => f.id === selectedFactoryId);

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Left Panel - Factory Tree */}
      <FactoryTree
        factories={mockFactories}
        selectedFactoryId={selectedFactoryId}
        onSelectFactory={handleSelectFactory}
        onCreateNew={handleCreateNew}
        isLoading={isLoading}
      />

      {/* Right Panel - Factory Details */}
      <div className="flex-1 p-8 overflow-y-auto">
        {selectedFactory ? (
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {selectedFactory.plant_name}
            </h1>
            <p className="text-lg text-gray-600 mb-6">{selectedFactory.company_name}</p>

            {/* Status Badge */}
            <div className="mb-8">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  selectedFactory.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {selectedFactory.is_active ? '稼働中' : '停止中'}
              </span>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-500 mb-1">工場ID</div>
                <div className="text-xl font-semibold">{selectedFactory.factory_id}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-500 mb-1">ライン数</div>
                <div className="text-xl font-semibold">{selectedFactory.lines_count}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-500 mb-1">従業員数</div>
                <div className="text-xl font-semibold">{selectedFactory.employees_count}名</div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                編集
              </button>
              <button className="px-6 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                詳細を表示
              </button>
              <button className="px-6 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                契約書を作成
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-gray-500 mb-4">工場を選択してください</p>
              <button
                onClick={handleCreateNew}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                新規工場を登録
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}