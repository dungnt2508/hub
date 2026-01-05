'use client';

import { useState, useEffect } from 'react';
import adminConfigService from '@/services/admin-config.service';
import { ChevronDown, Check } from 'lucide-react';

interface UseCase {
  intent: string;
  display_name: string;
  description: string;
  intent_type: string;
  domain: string;
  domain_display_name: string;
}

interface UseCaseSelectorProps {
  value?: string;
  onChange?: (intent: string, domain: string, intentType: string) => void;
  domainFilter?: string;
  intentTypeFilter?: string;
}

export default function UseCaseSelector({
  value,
  onChange,
  domainFilter,
  intentTypeFilter,
}: UseCaseSelectorProps) {
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadUseCases();
  }, [domainFilter, intentTypeFilter]);

  const loadUseCases = async () => {
    try {
      setLoading(true);
      const response = await adminConfigService.listUseCases();
      let allIntents = response.intents || [];

      // Filter by domain if provided
      if (domainFilter) {
        allIntents = allIntents.filter((uc) => uc.domain === domainFilter);
      }

      // Filter by intent type if provided
      if (intentTypeFilter) {
        allIntents = allIntents.filter((uc) => uc.intent_type === intentTypeFilter);
      }

      setUseCases(allIntents);
    } catch (error: any) {
      console.error('Failed to load use cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredUseCases = useCases.filter(
    (uc) =>
      uc.intent.toLowerCase().includes(searchTerm.toLowerCase()) ||
      uc.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      uc.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedUseCase = useCases.find((uc) => uc.intent === value);

  const handleSelect = (useCase: UseCase) => {
    if (onChange) {
      onChange(useCase.intent, useCase.domain, useCase.intent_type);
    }
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white text-left flex items-center justify-between"
      >
        <span className={selectedUseCase ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
          {selectedUseCase ? `${selectedUseCase.display_name} (${selectedUseCase.intent})` : 'Chọn use case...'}
        </span>
        <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-96 overflow-hidden">
            <div className="p-2 border-b border-gray-200 dark:border-gray-700">
              <input
                type="text"
                placeholder="Tìm kiếm use case..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                autoFocus
              />
            </div>
            <div className="overflow-y-auto max-h-80">
              {loading ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  Đang tải...
                </div>
              ) : filteredUseCases.length === 0 ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  Không tìm thấy use case nào
                </div>
              ) : (
                filteredUseCases.map((useCase) => (
                  <button
                    key={`${useCase.domain}-${useCase.intent}`}
                    type="button"
                    onClick={() => handleSelect(useCase)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                      value === useCase.intent ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {useCase.display_name}
                          </p>
                          {value === useCase.intent && (
                            <Check className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {useCase.description}
                        </p>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                            {useCase.domain_display_name}
                          </span>
                          <span className="text-xs px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400">
                            {useCase.intent_type}
                          </span>
                        </div>
                        <code className="text-xs text-gray-500 dark:text-gray-400 mt-1 block">
                          {useCase.intent}
                        </code>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

