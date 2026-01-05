'use client';

import { useState, useEffect } from 'react';
import adminConfigService from '@/services/admin-config.service';
import { Code, Database, Zap, Brain, MessageSquare } from 'lucide-react';

interface UseCase {
  intent: string;
  display_name: string;
  description: string;
  intent_type: string;
  domain: string;
  domain_display_name: string;
}

interface Domain {
  name: string;
  display_name: string;
  description: string;
  intents: Array<{
    intent: string;
    display_name: string;
    description: string;
    intent_type: string;
  }>;
}

export default function UseCaseList() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [intents, setIntents] = useState<UseCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  useEffect(() => {
    loadUseCases();
  }, []);

  const loadUseCases = async () => {
    try {
      setLoading(true);
      const response = await adminConfigService.listUseCases();
      if (response.domains) {
        setDomains(response.domains);
      }
      if (response.intents) {
        setIntents(response.intents);
      }
    } catch (error: any) {
      console.error('Failed to load use cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIntentTypeIcon = (intentType: string) => {
    switch (intentType) {
      case 'OPERATION':
        return <Zap className="h-4 w-4 text-blue-500" />;
      case 'KNOWLEDGE':
        return <Brain className="h-4 w-4 text-green-500" />;
      case 'META':
        return <MessageSquare className="h-4 w-4 text-purple-500" />;
      default:
        return <Code className="h-4 w-4 text-gray-500" />;
    }
  };

  const getIntentTypeColor = (intentType: string) => {
    switch (intentType) {
      case 'OPERATION':
        return 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400';
      case 'KNOWLEDGE':
        return 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400';
      case 'META':
        return 'bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400';
    }
  };

  const filteredIntents = selectedDomain
    ? intents.filter((intent) => intent.domain === selectedDomain)
    : intents;

  if (loading) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        Đang tải use cases...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Domain Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedDomain(null)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            selectedDomain === null
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
          }`}
        >
          Tất cả ({intents.length})
        </button>
        {domains.map((domain) => {
          const domainIntentCount = intents.filter((i) => i.domain === domain.name).length;
          return (
            <button
              key={domain.name}
              onClick={() => setSelectedDomain(domain.name)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedDomain === domain.name
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {domain.display_name} ({domainIntentCount})
            </button>
          );
        })}
      </div>

      {/* Use Cases List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredIntents.map((useCase) => (
          <div
            key={`${useCase.domain}-${useCase.intent}`}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  {getIntentTypeIcon(useCase.intent_type)}
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {useCase.display_name}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {useCase.description}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                  {useCase.domain_display_name}
                </span>
                <span
                  className={`text-xs px-2 py-1 rounded ${getIntentTypeColor(useCase.intent_type)}`}
                >
                  {useCase.intent_type}
                </span>
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <code className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                {useCase.intent}
              </code>
            </div>
          </div>
        ))}
      </div>

      {filteredIntents.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          Không có use case nào
        </div>
      )}
    </div>
  );
}

