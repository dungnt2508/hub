'use client';

import { UseCaseMetadata } from '@/services/dba-use-cases.service';
import { Table, BarChart3, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { useMemo } from 'react';

interface ResultViewerProps {
  useCase: UseCaseMetadata | null;
  result: any;
  error: string | null;
  executing?: boolean;
}

export function ResultViewer({ useCase, result, error, executing = false }: ResultViewerProps) {
  // Determine result type and structure from output_schema
  const resultStructure = useMemo(() => {
    if (!result || !useCase?.output_schema) return null;

    // Try to extract data from pipeline result
    const pipeline = result.pipeline || result;
    
    // Check for execution results (raw table data)
    if (pipeline.execution_results?.results) {
      return {
        type: 'table',
        data: pipeline.execution_results.results,
        columns: pipeline.execution_results.columns || [],
      };
    }

    // Check for interpretation (text/findings)
    if (pipeline.interpretation) {
      return {
        type: 'text',
        data: pipeline.interpretation,
      };
    }

    // Check for risk assessment
    if (pipeline.risk_assessment) {
      return {
        type: 'risk',
        data: pipeline.risk_assessment,
      };
    }

    // Default: try to render as table if it's an array
    if (Array.isArray(pipeline)) {
      return {
        type: 'table',
        data: pipeline,
        columns: pipeline.length > 0 ? Object.keys(pipeline[0]) : [],
      };
    }

    return null;
  }, [result, useCase]);

  const renderTable = (data: any[], columns: string[]) => {
    if (data.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No data available
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {data.slice(0, 100).map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-3 text-sm text-gray-900 dark:text-white"
                  >
                    {typeof row[col] === 'object'
                      ? JSON.stringify(row[col])
                      : String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 100 && (
          <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700">
            Showing first 100 rows of {data.length.toLocaleString()} total
          </div>
        )}
      </div>
    );
  };

  const renderText = (data: any) => {
    if (typeof data === 'string') {
      return (
        <div className="prose dark:prose-invert max-w-none">
          <pre className="whitespace-pre-wrap text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            {data}
          </pre>
        </div>
      );
    }

    if (typeof data === 'object') {
      return (
        <div className="space-y-3">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="border-b border-gray-200 dark:border-gray-700 pb-2">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                {key}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </p>
            </div>
          ))}
        </div>
      );
    }

    return <div className="text-sm text-gray-600 dark:text-gray-400">{String(data)}</div>;
  };

  const renderRiskAssessment = (data: any) => {
    return (
      <div className="space-y-3">
        {data.final_decision && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <div className="text-sm font-semibold text-blue-800 dark:text-blue-300">
              Decision: {data.final_decision}
            </div>
          </div>
        )}
        {data.gates && data.gates.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Security Gates
            </h4>
            {data.gates.map((gate: any, idx: number) => (
              <div
                key={idx}
                className={`p-2 rounded ${
                  gate.status === 'PASS'
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : gate.status === 'BLOCK'
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : 'bg-yellow-50 dark:bg-yellow-900/20'
                }`}
              >
                <div className="text-xs font-medium">{gate.gate_name}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {gate.reason}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Results
        </h3>
      </div>

      <div className="p-4">
        {error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-red-800 dark:text-red-300">
                  Error
                </h4>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                  {error}
                </p>
              </div>
            </div>
          </div>
        ) : !result ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No results yet</p>
            <p className="text-xs mt-1">Execute a use case to see results</p>
          </div>
        ) : resultStructure ? (
          <div className="space-y-4">
            {resultStructure.type === 'table' && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <Table className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Table Data ({resultStructure.data.length} rows)
                  </span>
                </div>
                {renderTable(resultStructure.data, resultStructure.columns)}
              </div>
            )}

            {resultStructure.type === 'text' && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Interpretation
                  </span>
                </div>
                {renderText(resultStructure.data)}
              </div>
            )}

            {resultStructure.type === 'risk' && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <AlertCircle className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Risk Assessment
                  </span>
                </div>
                {renderRiskAssessment(resultStructure.data)}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <pre className="text-xs bg-gray-50 dark:bg-gray-700 p-4 rounded-lg overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

