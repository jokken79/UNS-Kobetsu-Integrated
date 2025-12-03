'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FactoryTree } from '@/components/factory/FactoryTree';
import { useFactoryList, useFactory } from '@/hooks/useFactories';
import {
  BuildingOfficeIcon,
  MapPinIcon,
  UserGroupIcon,
  CogIcon,
  DocumentDuplicateIcon,
  PencilSquareIcon,
} from '@heroicons/react/24/outline';

/**
 * Factory Management Page with split view
 * Left panel: FactoryTree for navigation
 * Right panel: Selected factory details and actions
 */
export default function FactoryManagePage() {
  const router = useRouter();
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(null);

  // Fetch all factories for the tree
  const { data: factories = [], isLoading: isLoadingList } = useFactoryList();

  // Fetch selected factory details
  const { data: selectedFactory, isLoading: isLoadingDetails } = useFactory(selectedFactoryId);

  const handleCreateNew = () => {
    router.push('/factories/create');
  };

  const handleSelectFactory = (factoryId: number) => {
    setSelectedFactoryId(factoryId);
  };

  const handleEditFactory = () => {
    if (selectedFactoryId) {
      router.push(`/factories/${selectedFactoryId}/edit`);
    }
  };

  const handleCreateContract = () => {
    if (selectedFactoryId) {
      router.push(`/kobetsu/create?factory_id=${selectedFactoryId}`);
    }
  };

  return (
    <div className="h-[calc(100vh-64px)] flex">
      {/* Left Panel - Factory Tree */}
      <FactoryTree
        factories={factories}
        selectedFactoryId={selectedFactoryId}
        onSelectFactory={handleSelectFactory}
        onCreateNew={handleCreateNew}
        isLoading={isLoadingList}
      />

      {/* Right Panel - Factory Details */}
      <div className="flex-1 bg-gray-50 overflow-y-auto">
        {isLoadingDetails ? (
          <div className="p-8">
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse" />
              <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse" />
              <div className="grid grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-white rounded-lg shadow animate-pulse" />
                ))}
              </div>
            </div>
          </div>
        ) : selectedFactory ? (
          <div className="p-8">
            <div className="max-w-4xl mx-auto">
              {/* Header */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">{selectedFactory.plant_name}</h1>
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
                <p className="text-lg text-gray-600">{selectedFactory.company_name}</p>
                {selectedFactory.factory_id && (
                  <p className="text-sm text-gray-500 mt-1">ID: {selectedFactory.factory_id}</p>
                )}
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center">
                    <CogIcon className="h-10 w-10 text-gray-400" />
                    <div className="ml-4">
                      <div className="text-sm text-gray-500">ライン数</div>
                      <div className="text-2xl font-semibold text-gray-900">
                        {selectedFactory.lines.length}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center">
                    <UserGroupIcon className="h-10 w-10 text-gray-400" />
                    <div className="ml-4">
                      <div className="text-sm text-gray-500">従業員数</div>
                      <div className="text-2xl font-semibold text-gray-900">
                        {selectedFactory.employees_count}名
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center">
                    <DocumentDuplicateIcon className="h-10 w-10 text-gray-400" />
                    <div className="ml-4">
                      <div className="text-sm text-gray-500">契約タイプ</div>
                      <div className="text-sm font-medium text-gray-900">
                        {selectedFactory.conflict_date || '標準契約'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Factory Information */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">工場情報</h2>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedFactory.company_address && (
                    <>
                      <dt className="text-sm text-gray-500">本社住所</dt>
                      <dd className="text-sm text-gray-900">{selectedFactory.company_address}</dd>
                    </>
                  )}
                  {selectedFactory.plant_address && (
                    <>
                      <dt className="text-sm text-gray-500">工場住所</dt>
                      <dd className="text-sm text-gray-900">{selectedFactory.plant_address}</dd>
                    </>
                  )}
                  {selectedFactory.company_phone && (
                    <>
                      <dt className="text-sm text-gray-500">電話番号</dt>
                      <dd className="text-sm text-gray-900">{selectedFactory.company_phone}</dd>
                    </>
                  )}
                  {selectedFactory.dispatch_responsible_name && (
                    <>
                      <dt className="text-sm text-gray-500">派遣責任者</dt>
                      <dd className="text-sm text-gray-900">
                        {selectedFactory.dispatch_responsible_name}
                      </dd>
                    </>
                  )}
                </dl>
              </div>

              {/* Lines Section */}
              {selectedFactory.lines.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    生産ライン ({selectedFactory.lines.length})
                  </h2>
                  <div className="space-y-3">
                    {selectedFactory.lines
                      .filter((line) => line.is_active)
                      .map((line) => (
                        <div
                          key={line.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <div className="font-medium text-gray-900">{line.line_name}</div>
                            {line.department && (
                              <div className="text-sm text-gray-500">{line.department}</div>
                            )}
                          </div>
                          <div className="text-right">
                            {line.hourly_rate && (
                              <div className="text-sm text-gray-900">¥{line.hourly_rate}/h</div>
                            )}
                            {line.supervisor_name && (
                              <div className="text-xs text-gray-500">{line.supervisor_name}</div>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={handleEditFactory}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PencilSquareIcon className="h-5 w-5 mr-2" />
                  編集
                </button>
                <button
                  onClick={handleCreateContract}
                  className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <DocumentDuplicateIcon className="h-5 w-5 mr-2" />
                  個別契約書を作成
                </button>
                <button className="inline-flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  <UserGroupIcon className="h-5 w-5 mr-2" />
                  従業員を表示
                </button>
                <button className="inline-flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  <BuildingOfficeIcon className="h-5 w-5 mr-2" />
                  詳細レポート
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <BuildingOfficeIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-lg text-gray-500 mb-6">工場を選択してください</p>
              <button
                onClick={handleCreateNew}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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