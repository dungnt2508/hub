'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/AdminLayout';
import DBAExecutionPlaybook from '@/components/DBAExecutionPlaybook';
import dbaSandboxService, {
  Connection,
  RiskAssessmentResponse,
  DBATestSandboxRequest,
} from '@/services/dba-sandbox.service';
import dbaConnectionsService, { DatabaseConnection } from '@/services/dba-connections.service';
import dbaUseCasesService, { UseCaseMetadata } from '@/services/dba-use-cases.service';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  Database,
  Shield,
  Play,
  Lock,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface GateCheckResult {
  gate_name: string;
  status: 'PASS' | 'BLOCK' | 'WARN';
  reason: string;
}

/**
 * DBA Risk Simulation Dashboard
 * 
 * Purpose: Show DBA whether bot will GO or STOP, and why.
 * This is NOT a UI playground. This is a decision simulation interface.
 * 
 * Key principles:
 * 1. DECISION-FIRST: GO/NO-GO visible in 5 seconds
 * 2. PLAYBOOK-CENTRIC: Organized by DBA playbook, not SQL
 * 3. GATE-TRANSPARENT: All 4 hard gates shown clearly
 * 4. ENGINE-AWARE: DB type, environment, scope always visible
 * 5. NO AMBIGUITY: No progress bars, no scores, no "maybe"
 */
export default function DBASandboxPage() {
  // ============================================================
  // STATE: INPUT SECTION
  // ============================================================
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [useCases, setUseCases] = useState<UseCaseMetadata[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [customQuery, setCustomQuery] = useState<string>('');
  const [useCustomQuery, setUseCustomQuery] = useState(false);
  const [connectionsLoading, setConnectionsLoading] = useState(true);
  const [useCasesLoading, setUseCasesLoading] = useState(true);

  // ============================================================
  // STATE: EXECUTION & RESULTS
  // ============================================================
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RiskAssessmentResponse | null>(null);
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [showPipelineModal, setShowPipelineModal] = useState(false);

  // ============================================================
  // LOAD DATA
  // ============================================================
  useEffect(() => {
    loadConnections();
    loadUseCases();
  }, []);

  const loadConnections = async () => {
    try {
      setConnectionsLoading(true);
      const response = await dbaConnectionsService.listConnections({ status: 'active' });
      const conns = (response as any).items || [];
      setConnections(conns);

      if (conns.length > 0) {
        const activeConn = conns.find((c: DatabaseConnection) => c.status === 'active');
        setSelectedConnectionId(activeConn?.connection_id || conns[0].connection_id);
      }
    } catch (error: any) {
      console.error('Failed to load connections:', error);
    } finally {
      setConnectionsLoading(false);
    }
  };

  const loadUseCases = async () => {
    try {
      setUseCasesLoading(true);
      const cases = await dbaUseCasesService.listUseCases();
      console.log('🎯 Loaded use cases:', cases);
      setUseCases(cases);

      if (cases.length > 0) {
        setSelectedUseCase(cases[0].id);
      }
    } catch (error: any) {
      console.error('❌ Failed to load use cases:', error);
      toast.error(`Failed to load use cases: ${error.message}`);
    } finally {
      setUseCasesLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    if (!selectedConnectionId) {
      toast.error('Select a database connection');
      return;
    }

    if (!selectedUseCase && !customQuery) {
      toast.error('Select a playbook or provide custom SQL');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const request: DBATestSandboxRequest = {
        connection_id: selectedConnectionId,
        scenario: !useCustomQuery ? selectedUseCase : undefined,
        sql_query: useCustomQuery ? customQuery : undefined,
      };

      const assessment = await dbaSandboxService.runRiskAssessment(request);
      setResult(assessment);
      toast.success('Risk simulation completed');
    } catch (error: any) {
      toast.error(error.message || 'Simulation failed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleExecutePlaybook = async () => {
    if (!selectedConnectionId || !selectedUseCase) {
      toast.error('Select a connection and playbook');
      return;
    }

    setPipelineLoading(true);
    setPipelineResult(null);

    try {
      const response = await dbaSandboxService.executePlaybook(
        selectedConnectionId,
        selectedUseCase
      );
      
      if (response.pipeline) {
        setPipelineResult(response.pipeline);
        setShowPipelineModal(true);
        toast.success('Playbook execution completed');
      } else if (response.status === 'blocked') {
        toast.error('Execution blocked by risk assessment: ' + response.reason);
      } else {
        toast.error('Unexpected response format');
      }
    } catch (error: any) {
      toast.error(error.message || 'Playbook execution failed');
      console.error(error);
    } finally {
      setPipelineLoading(false);
    }
  };

  const selectedConnection = connections.find((c) => c.connection_id === selectedConnectionId);

  /**
   * Render Decision Status
   * CRITICAL: This must be visible at top, no collapse
   */
  const renderDecisionStatus = () => {
    if (!result) return null;

    // Determine final decision based on gates
    const blockedGates = (result.gates || []).filter((g) => g.status === 'BLOCK');
    const isFinalDecisionGO = blockedGates.length === 0;

    return (
      <div
        className={`border-2 p-6 rounded-lg font-mono ${
          isFinalDecisionGO
            ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
            : 'border-red-500 bg-red-50 dark:bg-red-900/20'
        }`}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">
            FINAL DECISION: {isFinalDecisionGO ? '✅ GO' : '❌ NO-GO'}
          </h2>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            {new Date(result.trace.timestamp).toLocaleTimeString()}
          </div>
        </div>

        {!isFinalDecisionGO && blockedGates.length > 0 && (
          <div className="bg-red-100 dark:bg-red-900/50 border-l-4 border-red-500 p-4 rounded">
            <div className="font-semibold text-red-900 dark:text-red-100 mb-2">
              BLOCKED BY:
            </div>
            <ul className="space-y-1 text-sm">
              {blockedGates.map((gate, idx) => (
                <li key={idx} className="text-red-800 dark:text-red-200 flex items-start">
                  <span className="text-red-600 dark:text-red-400 mr-2 font-bold">✗</span>
                  <span>
                    <strong>{gate.gate_name}:</strong> {gate.reason}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {isFinalDecisionGO && (result.gates || []).length > 0 && (
          <div className="text-sm text-green-700 dark:text-green-300">
            All {(result.gates || []).length} gates passed. Safe to proceed.
          </div>
        )}
      </div>
    );
  };

  /**
   * Render Environment & Scope Context
   * CRITICAL: Always visible so DBA knows WHERE this will run
   */
  const renderEnvironmentContext = () => {
    if (!selectedConnection) return null;

    const isProduction =
      selectedConnection.name?.toLowerCase().includes('prod') ||
      selectedConnection.environment?.toLowerCase().includes('prod');

    return (
      <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-300 dark:border-gray-700 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <Database className="h-4 w-4 mr-2" />
          TARGET ENVIRONMENT & SCOPE
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600 dark:text-gray-400">Connection</div>
            <div className="font-mono text-gray-900 dark:text-white">{selectedConnection.name}</div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400">Environment</div>
            <div
              className={`font-mono font-bold ${
                isProduction
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-green-600 dark:text-green-400'
              }`}
            >
              {isProduction ? '🔴 PRODUCTION' : '🟢 NON-PROD'}
            </div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400">Database Engine</div>
            <div className="font-mono text-gray-900 dark:text-white">
              {selectedConnection.db_type?.toUpperCase()}
            </div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400">Status</div>
            <div
              className={`font-mono ${
                selectedConnection.status === 'active'
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {selectedConnection.status || 'unknown'}
            </div>
          </div>
        </div>
      </div>
    );
  };

  /**
   * Render Hard Gates - Must be clear (PASS/BLOCK), no collapse
   */
  const renderHardGates = () => {
    if (!result || !result.gates) return null;

    return (
      <div className="space-y-3">
        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center">
          <Shield className="h-4 w-4 mr-2" />
          HARD GATES (Decision Checkpoints)
        </h3>

        {result.gates.map((gate, idx) => (
          <div
            key={idx}
            className={`border-l-4 p-3 rounded-r ${
              gate.status === 'PASS'
                ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
                : gate.status === 'BLOCK'
                  ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                  : 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  {gate.status === 'PASS' && <span>✓</span>}
                  {gate.status === 'BLOCK' && <span>✗</span>}
                  {gate.status === 'WARN' && <span>⚠</span>} {gate.gate_name}
                </div>
                <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                  {gate.reason}
                </div>
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {gate.status}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  /**
   * Render Playbook Context
   */
  const renderPlaybookContext = () => {
    if (!selectedUseCase || useCustomQuery) return null;

    const usecase = useCases.find((u) => u.id === selectedUseCase);
    if (!usecase) return null;

    return (
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
          {usecase.name}
        </h3>
        <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">{usecase.description}</p>
        {usecase.required_slots && usecase.required_slots.length > 0 && (
          <div className="text-xs text-blue-700 dark:text-blue-400">
            <strong>Intent:</strong> {usecase.intent}
          </div>
        )}
      </div>
    );
  };

  /**
   * Render Execution Trace - Always expanded for critical decisions
   */
  const renderExecutionTrace = () => {
    if (!result || !result.trace) return null;

    return (
      <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-300 dark:border-gray-700 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <AlertCircle className="h-4 w-4 mr-2" />
          EXECUTION TRACE (Gate-by-Gate Checklist)
        </h3>

        <div className="space-y-2 font-mono text-sm">
          {result.trace.steps.map((step, idx) => (
            <div key={idx} className="flex items-start justify-between p-2 bg-white dark:bg-gray-800 rounded">
              <div className="flex items-start flex-1">
                {step.result === 'pass' && (
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                )}
                {step.result === 'fail' && (
                  <XCircle className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                )}
                {step.result === 'warn' && (
                  <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                )}
                <span className="text-gray-700 dark:text-gray-300">{step.step}</span>
              </div>
              <div className="text-gray-500 dark:text-gray-500 text-xs ml-2 flex-shrink-0">
                {step.duration_ms}ms
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-300 dark:border-gray-700 mt-3 pt-3 text-xs text-gray-600 dark:text-gray-400">
          Total: {result.trace.duration_ms}ms
        </div>
      </div>
    );
  };

  /**
   * Main Render
   */
  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            DBA Bot - Risk Simulation
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Test whether bot will GO or STOP before running on production
          </p>
        </div>

        {/* ============================================================
            INPUT SECTION
            ============================================================ */}
        <div className="space-y-4">
          {/* Step 1: Connection Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Step 1: Select Target Database
            </h2>

            {connectionsLoading ? (
              <div className="text-center py-4 text-gray-500">Loading connections...</div>
            ) : connections.length === 0 ? (
              <div className="text-center py-4 text-yellow-600">
                No active connections. Create one first.
              </div>
            ) : (
              <div className="space-y-2">
                {connections.map((conn) => (
                  <label
                    key={conn.connection_id}
                    className={`flex items-start p-3 border rounded cursor-pointer transition ${
                      selectedConnectionId === conn.connection_id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="connection"
                      value={conn.connection_id}
                      checked={selectedConnectionId === conn.connection_id}
                      onChange={(e) => setSelectedConnectionId(e.target.value)}
                      className="mt-1"
                    />
                    <div className="ml-3 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {conn.name}
                        </span>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            conn.status === 'active'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/50'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/50'
                          }`}
                        >
                          {conn.status}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {conn.db_type?.toUpperCase()} • {conn.environment || 'unknown'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Step 2: Playbook Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Step 2: Select DBA Playbook
            </h2>

            {useCasesLoading ? (
              <div className="text-center py-4 text-gray-500">Loading playbooks...</div>
            ) : useCases.length === 0 ? (
              <div className="text-center py-4 text-gray-500">No playbooks available</div>
            ) : (
              <div className="space-y-3">
                <div className="space-y-2">
                  {useCases.map((usecase) => (
                    <label
                      key={usecase.id}
                      className={`flex items-start p-3 border rounded cursor-pointer transition ${
                        selectedUseCase === usecase.id && !useCustomQuery
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="playbook"
                        value={usecase.id}
                        checked={selectedUseCase === usecase.id && !useCustomQuery}
                        onChange={() => {
                          setSelectedUseCase(usecase.id);
                          setUseCustomQuery(false);
                        }}
                        className="mt-1"
                      />
                      <div className="ml-3 flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {usecase.name}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {usecase.description}
                        </div>
                        <div className="text-xs text-gray-500 mt-2 font-mono">
                          intent: {usecase.intent}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                {/* Custom SQL Option */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <label className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      checked={useCustomQuery}
                      onChange={(e) => setUseCustomQuery(e.target.checked)}
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Test custom SQL validation
                    </span>
                  </label>

                  {useCustomQuery && (
                    <textarea
                      value={customQuery}
                      onChange={(e) => setCustomQuery(e.target.value)}
                      placeholder="Paste SQL query here"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white font-mono text-sm"
                      rows={4}
                    />
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Run Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleRunSimulation}
              disabled={loading || !selectedConnectionId || (!selectedUseCase && !customQuery)}
              className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Play className="h-4 w-4 mr-2" />
              {loading ? 'Running simulation...' : 'Run Risk Simulation'}
            </button>

            {/* Execute Playbook Button - Only shown if GO decision and use_case selected */}
            {result && result.final_decision !== 'NO-GO' && selectedUseCase && !useCustomQuery && (
              <button
                onClick={handleExecutePlaybook}
                disabled={pipelineLoading}
                className="flex items-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <Zap className="h-4 w-4 mr-2" />
                {pipelineLoading ? 'Executing...' : 'Execute Playbook'}
              </button>
            )}
          </div>
        </div>

        {/* ============================================================
            RESULTS SECTION
            ============================================================ */}
        {result && (
          <div className="space-y-4">
            {/* 1. FINAL DECISION (TOP, NO COLLAPSE) */}
            {renderDecisionStatus()}

            {/* 2. ENVIRONMENT CONTEXT */}
            {renderEnvironmentContext()}

            {/* 3. HARD GATES (NO COLLAPSE) */}
            {renderHardGates()}

            {/* 4. PLAYBOOK CONTEXT (if applicable) */}
            {renderPlaybookContext()}

            {/* 5. EXECUTION TRACE */}
            {renderExecutionTrace()}

            {/* Critical Issues */}
            {result.critical_issues.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <h3 className="font-semibold text-red-900 dark:text-red-200 mb-2 flex items-center">
                  <XCircle className="h-4 w-4 mr-2" />
                  Critical Issues ({result.critical_issues.length})
                </h3>
                <ul className="space-y-1 text-sm text-red-800 dark:text-red-200">
                  {result.critical_issues.map((issue, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2 font-bold">✗</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-2 flex items-center">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Warnings ({result.warnings.length})
                </h3>
                <ul className="space-y-1 text-sm text-yellow-800 dark:text-yellow-200">
                  {result.warnings.map((warning, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2">⚠</span>
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Pipeline Execution Modal */}
        {showPipelineModal && pipelineResult && (
          <DBAExecutionPlaybook
            pipelineData={pipelineResult}
            onClose={() => {
              setShowPipelineModal(false);
              setPipelineResult(null);
            }}
          />
        )}
      </div>
    </AdminLayout>
  );
}
