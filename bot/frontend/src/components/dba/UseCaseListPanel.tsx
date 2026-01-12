'use client';

import { UseCaseMetadata } from '@/services/dba-use-cases.service';
import { Loader2, Search } from 'lucide-react';
import { useState, useMemo } from 'react';

interface UseCaseListPanelProps {
  useCases: UseCaseMetadata[];
  selectedUseCase: UseCaseMetadata | null;
  onSelect: (useCase: UseCaseMetadata) => void;
  loading: boolean;
}

export function UseCaseListPanel({
  useCases,
  selectedUseCase,
  onSelect,
  loading,
}: UseCaseListPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredUseCases = useMemo(() => {
    if (!searchQuery.trim()) return useCases;
    
    const query = searchQuery.toLowerCase();
    return useCases.filter((uc) => {
      return (
        uc.name.toLowerCase().includes(query) ||
        uc.description.toLowerCase().includes(query) ||
        uc.id.toLowerCase().includes(query) ||
        (uc.tags || []).some((tag) => tag.toLowerCase().includes(query))
      );
    });
  }, [useCases, searchQuery]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Use Cases ({useCases.length})
        </h2>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search use cases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* List */}
      <div className="overflow-y-auto max-h-[calc(100vh-300px)]">
        {filteredUseCases.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            {searchQuery ? 'No use cases found' : 'No use cases available'}
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredUseCases.map((useCase) => {
              const isSelected = selectedUseCase?.id === useCase.id;
              return (
                <button
                  key={useCase.id}
                  onClick={() => onSelect(useCase)}
                  className={`w-full text-left p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                    isSelected
                      ? 'bg-primary-50 dark:bg-primary-900/20 border-l-4 border-primary-500'
                      : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-2xl">{useCase.icon}</span>
                    <div className="flex-1 min-w-0">
                      <h3
                        className={`font-medium ${
                          isSelected
                            ? 'text-primary-700 dark:text-primary-400'
                            : 'text-gray-900 dark:text-white'
                        }`}
                      >
                        {useCase.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                        {useCase.description}
                      </p>
                      {useCase.tags && useCase.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {useCase.tags.map((tag) => (
                            <span
                              key={tag}
                              className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

