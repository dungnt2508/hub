'use client';

import { UseCaseMetadata } from '@/services/dba-use-cases.service';
import { Play, Loader2, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface ExecutionPanelProps {
  useCase: UseCaseMetadata | null;
  connectionId: string;
  executing: boolean;
  onExecute: () => void;
  error: string | null;
}

export function ExecutionPanel({
  useCase,
  connectionId,
  executing,
  onExecute,
  error,
}: ExecutionPanelProps) {
  const canExecute = useCase && connectionId && !executing;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Execution
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Execution Limits Info */}
        {useCase?.execution_limits && (
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 space-y-1">
            <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300">
              Execution Limits
            </h4>
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
              {useCase.execution_limits.timeout_seconds && (
                <div>Timeout: {useCase.execution_limits.timeout_seconds}s</div>
              )}
              {useCase.execution_limits.max_rows && (
                <div>Max rows: {useCase.execution_limits.max_rows.toLocaleString()}</div>
              )}
            </div>
          </div>
        )}

        {/* Capability Flags */}
        {useCase?.capability_flags && (
          <div className="flex flex-wrap gap-2">
            {useCase.capability_flags.can_edit_query && (
              <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded">
                Query Editable
              </span>
            )}
            {useCase.capability_flags.can_export && (
              <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded">
                Exportable
              </span>
            )}
            {useCase.capability_flags.requires_approval && (
              <span className="text-xs px-2 py-1 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded">
                Requires Approval
              </span>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-800 dark:text-red-300">
                  Execution Error
                </h4>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                  {error}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Execute Button */}
        <button
          onClick={onExecute}
          disabled={!canExecute}
          className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
            canExecute
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          }`}
        >
          {executing ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <Play className="h-5 w-5" />
              <span>Execute Use Case</span>
            </>
          )}
        </button>

        {!useCase && (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Select a use case to execute
          </p>
        )}
        {!connectionId && (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Select a database connection
          </p>
        )}
      </div>
    </div>
  );
}

