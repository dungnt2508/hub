'use client';

import { UseCaseMetadata } from '@/services/dba-use-cases.service';
import { DatabaseConnection } from '@/services/dba-connections.service';
import { Loader2, Database as DatabaseIcon } from 'lucide-react';
import { useMemo } from 'react';

interface UseCaseDetailPanelProps {
  useCase: UseCaseMetadata;
  loading: boolean;
  connections: DatabaseConnection[];
  selectedConnectionId: string;
  onConnectionChange: (connectionId: string) => void;
  params: Record<string, any>;
  onParamsChange: (params: Record<string, any>) => void;
  queryOverrides: Record<string, string>;
  onQueryOverridesChange: (overrides: Record<string, string>) => void;
  hideConnectionSelector?: boolean;
}

export function UseCaseDetailPanel({
  useCase,
  loading,
  connections,
  selectedConnectionId,
  onConnectionChange,
  params,
  onParamsChange,
  queryOverrides,
  onQueryOverridesChange,
  hideConnectionSelector = false,
}: UseCaseDetailPanelProps) {
  // Render form fields from param_schema
  const renderParamFields = () => {
    if (!useCase.param_schema || !useCase.param_schema.properties) {
      return (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          No parameters required
        </div>
      );
    }

    const properties = useCase.param_schema.properties;
    const required = useCase.param_schema.required || [];

    return Object.entries(properties).map(([key, schema]: [string, any]) => {
      const isRequired = required.includes(key);
      const value = params[key] ?? schema.default ?? '';

      return (
        <div key={key} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {schema.title || key}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </label>
          {schema.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {schema.description}
            </p>
          )}

          {schema.type === 'string' && (
            <input
              type="text"
              value={value}
              onChange={(e) =>
                onParamsChange({ ...params, [key]: e.target.value })
              }
              placeholder={schema.placeholder || ''}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          )}

          {schema.type === 'number' && (
            <input
              type="number"
              value={value}
              onChange={(e) =>
                onParamsChange({
                  ...params,
                  [key]: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              min={schema.minimum}
              max={schema.maximum}
              step={schema.multipleOf || 1}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          )}

          {schema.type === 'boolean' && (
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={value || false}
                onChange={(e) =>
                  onParamsChange({ ...params, [key]: e.target.checked })
                }
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {schema.title || key}
              </span>
            </label>
          )}

          {schema.type === 'array' && schema.items && (
            <div className="space-y-2">
              {(value as any[] || []).map((item, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => {
                      const newArray = [...(value as any[] || [])];
                      newArray[idx] = e.target.value;
                      onParamsChange({ ...params, [key]: newArray });
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={() => {
                      const newArray = [...(value as any[] || [])];
                      newArray.splice(idx, 1);
                      onParamsChange({ ...params, [key]: newArray });
                    }}
                    className="px-2 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => {
                  const newArray = [...(value as any[] || []), ''];
                  onParamsChange({ ...params, [key]: newArray });
                }}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                + Add item
              </button>
            </div>
          )}
        </div>
      );
    }).filter(Boolean);
  };

  // Render query override controls (if editable_query_schema exists)
  const renderQueryOverrides = () => {
    if (!useCase.capability_flags?.can_edit_query || !useCase.query_templates) {
      return null;
    }

    const templates = useCase.query_templates.templates_by_db;
    const dbType = connections.find((c) => c.connection_id === selectedConnectionId)?.db_type || 'sqlserver';
    const dbTemplates = templates[dbType] || [];

    if (dbTemplates.length === 0) {
      return null;
    }

    return (
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Query Overrides (Optional)
        </h4>
        {dbTemplates.map((template) => {
          const stepKey = `step_${template.step_number}`;
          const overrideValue = queryOverrides[stepKey] || '';

          return (
            <div key={template.step_number} className="space-y-1">
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400">
                Step {template.step_number}: {template.purpose}
                {template.read_only && (
                  <span className="ml-2 text-xs text-gray-500">(Read-only)</span>
                )}
              </label>
              {template.description && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {template.description}
                </p>
              )}
              {!template.read_only && (
                <textarea
                  value={overrideValue}
                  onChange={(e) =>
                    onQueryOverridesChange({
                      ...queryOverrides,
                      [stepKey]: e.target.value,
                    })
                  }
                  placeholder="Leave empty to use default query"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              )}
            </div>
          );
        })}
      </div>
    );
  };

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
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{useCase.icon}</span>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {useCase.name}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {useCase.description}
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Connection Selector */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Database Connection <span className="text-red-500">*</span>
          </label>
          <select
            value={selectedConnectionId}
            onChange={(e) => onConnectionChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select connection...</option>
            {connections.map((conn) => (
              <option key={conn.connection_id} value={conn.connection_id}>
                {conn.name || conn.connection_id} ({conn.db_type})
              </option>
            ))}
          </select>
        </div>

        {/* Parameters */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Parameters
          </h4>
          <div className="space-y-3">{renderParamFields()}</div>
        </div>
      </div>
    </div>
  );
}

