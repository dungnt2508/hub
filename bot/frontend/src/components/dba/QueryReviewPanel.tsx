'use client';

import { UseCaseMetadata } from '@/services/dba-use-cases.service';
import { DatabaseConnection } from '@/services/dba-connections.service';
import { FileText, Eye, EyeOff } from 'lucide-react';
import { useState, useMemo } from 'react';

interface QueryReviewPanelProps {
  useCase: UseCaseMetadata;
  connections: DatabaseConnection[];
  selectedConnectionId: string;
  queryOverrides: Record<string, string>;
}

export function QueryReviewPanel({
  useCase,
  connections,
  selectedConnectionId,
  queryOverrides,
}: QueryReviewPanelProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [showAllQueries, setShowAllQueries] = useState(false);

  // Get queries for selected connection's DB type
  const queries = useMemo(() => {
    if (!useCase.query_templates || !selectedConnectionId) return [];

    const connection = connections.find((c) => c.connection_id === selectedConnectionId);
    if (!connection) return [];

    const dbType = connection.db_type === 'sql_server' ? 'sqlserver' : connection.db_type;
    const dbTemplates = useCase.query_templates.templates_by_db[dbType] || [];

    return dbTemplates.map((template) => {
      const stepKey = `step_${template.step_number}`;
      const overrideQuery = queryOverrides[stepKey];
      const finalQuery = overrideQuery || (template as any).query_text || '';

      return {
        stepNumber: template.step_number,
        purpose: template.purpose,
        description: template.description,
        readOnly: template.read_only,
        query: finalQuery,
        isOverridden: !!overrideQuery,
      };
    });
  }, [useCase, connections, selectedConnectionId, queryOverrides]);

  const toggleStep = (stepNumber: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber);
    } else {
      newExpanded.add(stepNumber);
    }
    setExpandedSteps(newExpanded);
  };

  const expandAll = () => {
    if (showAllQueries) {
      setExpandedSteps(new Set());
      setShowAllQueries(false);
    } else {
      setExpandedSteps(new Set(queries.map((q) => q.stepNumber)));
      setShowAllQueries(true);
    }
  };

  if (!useCase.query_templates || queries.length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Query Review
          </h3>
        </div>
        <button
          onClick={expandAll}
          className="text-sm text-primary-600 hover:text-primary-700 flex items-center space-x-1"
        >
          {showAllQueries ? (
            <>
              <EyeOff className="h-4 w-4" />
              <span>Collapse All</span>
            </>
          ) : (
            <>
              <Eye className="h-4 w-4" />
              <span>Expand All</span>
            </>
          )}
        </button>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {queries.map((query) => {
          const isExpanded = expandedSteps.has(query.stepNumber);
          const hasQuery = query.query.trim().length > 0;

          return (
            <div key={query.stepNumber} className="p-4">
              <button
                onClick={() => toggleStep(query.stepNumber)}
                className="w-full flex items-start justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-4 p-4 rounded-lg transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">
                      Step {query.stepNumber}
                    </span>
                    {query.isOverridden && (
                      <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded">
                        Overridden
                      </span>
                    )}
                    {query.readOnly && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded">
                        Read-only
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {query.purpose}
                  </p>
                  {query.description && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {query.description}
                    </p>
                  )}
                </div>
                <div className="ml-4 flex-shrink-0">
                  {isExpanded ? (
                    <span className="text-xs text-gray-500">Hide SQL</span>
                  ) : (
                    <span className="text-xs text-primary-600">Show SQL</span>
                  )}
                </div>
              </button>

              {isExpanded && hasQuery && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <pre className="text-xs font-mono text-gray-900 dark:text-gray-100 whitespace-pre-wrap overflow-x-auto">
                      {query.query}
                    </pre>
                  </div>
                  {query.isOverridden && (
                    <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
                      ⚠️ This query has been overridden from the default template
                    </p>
                  )}
                </div>
              )}

              {isExpanded && !hasQuery && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                    No query available for this step
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

