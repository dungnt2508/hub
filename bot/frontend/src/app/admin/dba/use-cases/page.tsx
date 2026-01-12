'use client';

/**
 * DBA Use Cases Page
 * 
 * Metadata-driven use case execution interface.
 */

import { useState, useEffect, useMemo } from 'react';
import AdminLayout from '@/components/AdminLayout';
import { UseCaseListPanel } from '@/components/dba/UseCaseListPanel';
import { UseCaseDetailPanel } from '@/components/dba/UseCaseDetailPanel';
import { ExecutionPanel } from '@/components/dba/ExecutionPanel';
import { ResultViewer } from '@/components/dba/ResultViewer';
import { QueryEditor } from '@/components/dba/QueryEditor';
import dbaUseCasesService, { UseCaseMetadata, ExecuteUseCaseRequest } from '@/services/dba-use-cases.service';
import dbaConnectionsService, { DatabaseConnection } from '@/services/dba-connections.service';
import { Database, Play, FileText, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';

type TabType = 'detail' | 'queries' | 'results';

export default function DBAUseCasesPage() {
  // State: Use Cases
  const [useCases, setUseCases] = useState<UseCaseMetadata[]>([]);
  const [selectedUseCase, setSelectedUseCase] = useState<UseCaseMetadata | null>(null);
  const [useCaseDetail, setUseCaseDetail] = useState<UseCaseMetadata | null>(null);
  const [loadingUseCases, setLoadingUseCases] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // State: Connections
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [loadingConnections, setLoadingConnections] = useState(true);

  // State: Execution
  const [executionParams, setExecutionParams] = useState<Record<string, any>>({});
  const [queryOverrides, setQueryOverrides] = useState<Record<string, string>>({});
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  // State: UI
  const [activeTab, setActiveTab] = useState<TabType>('detail');

  // Load initial data
  useEffect(() => {
    loadUseCases();
    loadConnections();
  }, []);

  // Load use case detail when selected
  useEffect(() => {
    if (selectedUseCase) {
      loadUseCaseDetail(selectedUseCase.id);
      setActiveTab('detail');
      setExecutionResult(null);
      setExecutionError(null);
    }
  }, [selectedUseCase]);

  const loadUseCases = async () => {
    try {
      setLoadingUseCases(true);
      const cases = await dbaUseCasesService.listUseCases();
      setUseCases(cases);
    } catch (error: any) {
      toast.error(`Failed to load use cases: ${error.message}`);
    } finally {
      setLoadingUseCases(false);
    }
  };

  const loadConnections = async () => {
    try {
      setLoadingConnections(true);
      const response = await dbaConnectionsService.listConnections({ status: 'active' }) as { items?: DatabaseConnection[] };
      const conns = response.items || [];
      setConnections(conns);
      if (conns.length > 0) {
        setSelectedConnectionId(conns[0].connection_id);
      }
    } catch (error: any) {
      toast.error(`Failed to load connections: ${error.message}`);
    } finally {
      setLoadingConnections(false);
    }
  };

  const loadUseCaseDetail = async (useCaseId: string) => {
    try {
      setLoadingDetail(true);
      const detail = await dbaUseCasesService.getUseCaseDetail(useCaseId);
      setUseCaseDetail(detail);
      
      // Initialize params from schema
      if (detail.param_schema) {
        const initialParams: Record<string, any> = {};
        const properties = detail.param_schema.properties || {};
        for (const [key, schema] of Object.entries(properties)) {
          if (schema && typeof schema === 'object' && 'default' in schema) {
            initialParams[key] = schema.default;
          }
        }
        setExecutionParams(initialParams);
      }
      
      // Reset query overrides
      setQueryOverrides({});
    } catch (error: any) {
      toast.error(`Failed to load use case detail: ${error.message}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleUseCaseSelect = (useCase: UseCaseMetadata) => {
    setSelectedUseCase(useCase);
    setExecutionResult(null);
    setExecutionError(null);
    setExecutionParams({});
    setQueryOverrides({});
  };

  const handleExecute = async () => {
    if (!selectedUseCase || !selectedConnectionId) {
      toast.error('Please select a use case and connection');
      return;
    }

    try {
      setExecuting(true);
      setExecutionError(null);
      setActiveTab('results'); // Switch to results tab

      const request: ExecuteUseCaseRequest = {
        use_case_id: selectedUseCase.id,
        connection_id: selectedConnectionId,
        params: executionParams,
        query_overrides: Object.keys(queryOverrides).length > 0 ? queryOverrides : undefined,
      };

      const result = await dbaUseCasesService.executeUseCase(request);
      setExecutionResult(result);
      toast.success('Use case executed successfully');
    } catch (error: any) {
      setExecutionError(error.message);
      toast.error(`Execution failed: ${error.message}`);
      setActiveTab('results'); // Show error in results tab
    } finally {
      setExecuting(false);
    }
  };

  // Prepare query steps for QueryEditor
  const querySteps = useMemo(() => {
    if (!useCaseDetail?.query_templates || !selectedConnectionId) return [];

    const connection = connections.find((c) => c.connection_id === selectedConnectionId);
    if (!connection) return [];

    const dbType = connection.db_type === 'sql_server' ? 'sqlserver' : connection.db_type;
    const dbTemplates = useCaseDetail.query_templates.templates_by_db[dbType] || [];

    return dbTemplates.map((template) => {
      const stepKey = `step_${template.step_number}`;
      const overrideQuery = queryOverrides[stepKey];
      const defaultQuery = (template as any).query_text || '';

      return {
        stepNumber: template.step_number,
        purpose: template.purpose,
        description: template.description,
        readOnly: template.read_only,
        query: overrideQuery || defaultQuery,
      };
    });
  }, [useCaseDetail, connections, selectedConnectionId, queryOverrides]);

  const hasQueryTemplates = useCaseDetail?.query_templates && querySteps.length > 0;

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              DBA Use Cases
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Metadata-driven use case execution - no hardcoding, works for all DB types
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar: Use Case List */}
          <div className="lg:col-span-1">
            <UseCaseListPanel
              useCases={useCases}
              selectedUseCase={selectedUseCase}
              onSelect={handleUseCaseSelect}
              loading={loadingUseCases}
            />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            {selectedUseCase ? (
              <div className="space-y-4">
                {/* Connection Selector - Always visible */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <Database className="h-5 w-5 text-gray-400" />
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Database Connection
                        </label>
                        <select
                          value={selectedConnectionId}
                          onChange={(e) => setSelectedConnectionId(e.target.value)}
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
                    </div>
                    <div className="ml-4">
                      <button
                        onClick={handleExecute}
                        disabled={!selectedConnectionId || executing}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                          selectedConnectionId && !executing
                            ? 'bg-primary-600 hover:bg-primary-700 text-white'
                            : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        <Play className="h-5 w-5" />
                        <span>{executing ? 'Executing...' : 'Execute'}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Tabs */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  {/* Tab Headers */}
                  <div className="border-b border-gray-200 dark:border-gray-700">
                    <nav className="flex space-x-1 px-4" aria-label="Tabs">
                      <button
                        onClick={() => setActiveTab('detail')}
                        className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                          activeTab === 'detail'
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                      >
                        <FileText className="h-4 w-4" />
                        <span>Details & Parameters</span>
                      </button>
                      {hasQueryTemplates && (
                        <button
                          onClick={() => setActiveTab('queries')}
                          className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'queries'
                              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                          }`}
                        >
                          <FileText className="h-4 w-4" />
                          <span>Query Editor</span>
                          {Object.keys(queryOverrides).length > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded">
                              {Object.keys(queryOverrides).length}
                            </span>
                          )}
                        </button>
                      )}
                      <button
                        onClick={() => setActiveTab('results')}
                        className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                          activeTab === 'results'
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                      >
                        <BarChart3 className="h-4 w-4" />
                        <span>Results</span>
                        {executionResult && (
                          <span className="ml-1 px-1.5 py-0.5 text-xs bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded">
                            Ready
                          </span>
                        )}
                      </button>
                    </nav>
                  </div>

                  {/* Tab Content */}
                  <div className="p-6">
                    {activeTab === 'detail' && (
                      <UseCaseDetailPanel
                        useCase={useCaseDetail || selectedUseCase}
                        loading={loadingDetail}
                        connections={connections}
                        selectedConnectionId={selectedConnectionId}
                        onConnectionChange={setSelectedConnectionId}
                        params={executionParams}
                        onParamsChange={setExecutionParams}
                        queryOverrides={queryOverrides}
                        onQueryOverridesChange={setQueryOverrides}
                        hideConnectionSelector
                      />
                    )}

                    {activeTab === 'queries' && hasQueryTemplates && (
                      <QueryEditor
                        steps={querySteps}
                        queryOverrides={queryOverrides}
                        onQueryOverridesChange={setQueryOverrides}
                      />
                    )}

                    {activeTab === 'results' && (
                      <ResultViewer
                        useCase={selectedUseCase}
                        result={executionResult}
                        error={executionError}
                        executing={executing}
                      />
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No use case selected
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Select a use case from the list to get started
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
