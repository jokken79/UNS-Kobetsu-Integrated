'use client';

import { useState, useMemo } from 'react';
import {
  ChevronRightIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { FactoryListItem } from '@/types';

interface FactoryTreeProps {
  factories: FactoryListItem[];
  selectedFactoryId: number | null;
  onSelectFactory: (factoryId: number) => void;
  onCreateNew: () => void;
  isLoading?: boolean;
}

interface CompanyGroup {
  companyName: string;
  factories: FactoryListItem[];
  totalCount: number;
}

export function FactoryTree({
  factories,
  selectedFactoryId,
  onSelectFactory,
  onCreateNew,
  isLoading = false,
}: FactoryTreeProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());

  // Group factories by company and filter by search
  const groupedFactories = useMemo(() => {
    const filtered = factories.filter((factory) => {
      const query = searchQuery.toLowerCase();
      return (
        factory.company_name.toLowerCase().includes(query) ||
        factory.plant_name.toLowerCase().includes(query)
      );
    });

    const groups = new Map<string, FactoryListItem[]>();
    filtered.forEach((factory) => {
      const existing = groups.get(factory.company_name) || [];
      groups.set(factory.company_name, [...existing, factory]);
    });

    const result: CompanyGroup[] = [];
    groups.forEach((factoriesInGroup, companyName) => {
      result.push({
        companyName,
        factories: factoriesInGroup.sort((a, b) => a.plant_name.localeCompare(b.plant_name)),
        totalCount: factoriesInGroup.length,
      });
    });

    return result.sort((a, b) => a.companyName.localeCompare(b.companyName));
  }, [factories, searchQuery]);

  // Auto-expand companies that have the selected factory
  useMemo(() => {
    if (selectedFactoryId) {
      const factory = factories.find((f) => f.id === selectedFactoryId);
      if (factory && !expandedCompanies.has(factory.company_name)) {
        setExpandedCompanies(new Set([...expandedCompanies, factory.company_name]));
      }
    }
  }, [selectedFactoryId, factories, expandedCompanies]);

  const toggleCompany = (companyName: string) => {
    const newExpanded = new Set(expandedCompanies);
    if (newExpanded.has(companyName)) {
      newExpanded.delete(companyName);
    } else {
      newExpanded.add(companyName);
    }
    setExpandedCompanies(newExpanded);
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="w-[280px] bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 h-full flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-slate-700">
          <div className="h-10 bg-gray-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
        <div className="flex-1 p-4 space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-8 bg-gray-200 dark:bg-slate-700 rounded animate-pulse" />
              <div className="ml-6 space-y-1">
                <div className="h-7 bg-gray-100 dark:bg-slate-700/50 rounded animate-pulse" />
                <div className="h-7 bg-gray-100 dark:bg-slate-700/50 rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-gray-200 dark:border-slate-700">
          <div className="h-10 bg-gray-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-[280px] bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 h-full flex flex-col">
      {/* Search Input */}
      <div className="p-4 border-b border-gray-200 dark:border-slate-700">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-400" />
          <input
            type="text"
            placeholder="検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 bg-gray-100 dark:bg-slate-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 rounded-lg border border-gray-300 dark:border-slate-600 focus:border-theme-600 focus:ring-1 focus:ring-theme-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto">
        {groupedFactories.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-slate-400">
            {searchQuery ? '検索結果がありません' : '工場が登録されていません'}
          </div>
        ) : (
          <div className="p-2">
            {groupedFactories.map((group) => {
              const isExpanded = expandedCompanies.has(group.companyName);

              return (
                <div key={group.companyName} className="mb-1">
                  {/* Company Header */}
                  <button
                    onClick={() => toggleCompany(group.companyName)}
                    className="w-full px-2 py-1.5 flex items-center justify-between text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-colors"
                    title={group.companyName}
                  >
                    <div className="flex items-center space-x-2 min-w-0 flex-1">
                      {isExpanded ? (
                        <ChevronDownIcon className="h-4 w-4 text-gray-500 dark:text-slate-400 flex-shrink-0" />
                      ) : (
                        <ChevronRightIcon className="h-4 w-4 text-gray-500 dark:text-slate-400 flex-shrink-0" />
                      )}
                      <span className="text-sm font-medium truncate">{group.companyName}</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-400 flex-shrink-0 ml-2">({group.totalCount})</span>
                  </button>

                  {/* Factories List */}
                  {isExpanded && (
                    <div className="ml-4 mt-1 space-y-0.5 transition-all duration-200">
                      {group.factories.map((factory) => {
                        const isSelected = factory.id === selectedFactoryId;
                        const isActive = factory.is_active;

                        return (
                          <button
                            key={factory.id}
                            onClick={() => onSelectFactory(factory.id)}
                            className={`w-full px-3 py-1.5 flex items-center space-x-2 rounded transition-colors ${
                              isSelected
                                ? 'bg-theme-600 text-white'
                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700'
                            }`}
                            title={`${factory.plant_name}${factory.lines_count > 0 ? ` (${factory.lines_count}ライン)` : ''}`}
                          >
                            <span
                              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                                isActive
                                  ? isSelected
                                    ? 'bg-white'
                                    : 'bg-green-500'
                                  : isSelected
                                  ? 'bg-gray-300'
                                  : 'bg-gray-500'
                              }`}
                            />
                            <span className="text-sm truncate min-w-0">{factory.plant_name}</span>
                            {factory.lines_count > 0 && (
                              <span
                                className={`text-xs ml-auto flex-shrink-0 ${
                                  isSelected ? 'text-white/70' : 'text-slate-500'
                                }`}
                              >
                                {factory.lines_count}ライン
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* New Factory Button */}
      <div className="p-4 border-t border-gray-200 dark:border-slate-700">
        <button
          onClick={onCreateNew}
          className="w-full px-4 py-2 bg-theme-600 text-white rounded-lg hover:bg-theme-700 transition-colors flex items-center justify-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>新規工場</span>
        </button>
      </div>
    </div>
  );
}