'use client';

import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Database,
  Zap,
  FileText,
  ChevronDown,
  Play,
  Shield,
} from 'lucide-react';

interface ExecutionStep {
  step: number;
  status: 'success' | 'failure' | 'timeout' | 'skipped';
  duration_ms: number;
  rows: number;
  columns: string[];
  data: Record<string, any>[];
  error?: string;
}

interface ExecutionResult {
  playbook: string;
  connection_id: string;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
  status: 'success' | 'partial_failure' | 'failure';
  step_results: ExecutionStep[];
  error?: string;
}

interface Finding {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  title: string;
  description: string;
  affected_objects?: string[];
}

interface Recommendation {
  type: 'safe' | 'risky' | 'blocked';
  description: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  estimated_impact?: string;
}

interface InterpretationResult {
  playbook: string;
  connection_id: string;
  generated_at: string;
  summary: string;
  findings: Finding[];
  risk_observations: string[];
  recommendations: Recommendation[];
  next_steps?: string;
  llm_model: string;
  processing_time_ms: number;
}

interface RiskAssessmentResult {
  final_decision: 'GO' | 'GO-WITH-CONDITIONS' | 'NO-GO';
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  decision_explanation: string;
  can_execute: boolean;
  gates: Array<{
    gate_name: string;
    status: 'PASS' | 'BLOCK' | 'WARN';
    reason: string;
  }>;
  critical_issues: string[];
  warnings: string[];
  checks_passed: Array<Record<string, any>>;
  recommendations: string[];
  trace: {
    timestamp: string;
    duration_ms: number;
    steps: Array<{
      step: string;
      duration_ms: number;
      result: 'pass' | 'fail' | 'warn';
    }>;
  };
}

interface PipelineExecutionData {
  request_id: string;
  playbook: string;
  connection_id: string;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
  pipeline_status: 'success' | 'failed' | 'stopped';
  stages: Array<{
    stage: string;
    status: 'success' | 'failure' | 'skipped';
    duration_ms: number;
    error?: string;
  }>;
  risk_assessment: RiskAssessmentResult;
  execution_plan: any;
  execution_results: ExecutionResult;
  interpretation: InterpretationResult;
}

interface Props {
  pipelineData: PipelineExecutionData;
  onClose: () => void;
}

export default function DBAExecutionPlaybook({ pipelineData, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<'risk' | 'execution' | 'interpretation'>('risk');
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  // RISK ASSESSMENT TAB
  const renderRiskTab = () => {
    const risk = pipelineData.risk_assessment;
    const statusColor = {
      'GO': 'bg-green-50 border-green-200',
      'GO-WITH-CONDITIONS': 'bg-yellow-50 border-yellow-200',
      'NO-GO': 'bg-red-50 border-red-200',
    };

    const statusTextColor = {
      'GO': 'text-green-700',
      'GO-WITH-CONDITIONS': 'text-yellow-700',
      'NO-GO': 'text-red-700',
    };

    const statusIcon = {
      'GO': <CheckCircle className="w-5 h-5 text-green-600" />,
      'GO-WITH-CONDITIONS': <AlertCircle className="w-5 h-5 text-yellow-600" />,
      'NO-GO': <AlertCircle className="w-5 h-5 text-red-600" />,
    };

    return (
      <div className="space-y-4">
        {/* Decision Box */}
        <div className={`p-6 border rounded-lg ${statusColor[risk.final_decision]}`}>
          <div className="flex items-center gap-3 mb-4">
            {statusIcon[risk.final_decision]}
            <h2 className={`text-2xl font-bold ${statusTextColor[risk.final_decision]}`}>
              {risk.final_decision}
            </h2>
          </div>
          <p className="text-sm text-gray-700 mb-2">{risk.decision_explanation}</p>
          <div className="flex gap-2">
            <span className="inline-block px-3 py-1 bg-white bg-opacity-70 rounded text-sm font-medium">
              Risk Level: {risk.risk_level}
            </span>
          </div>
        </div>

        {/* Gates */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5" /> 4 Hard Gates
          </h3>
          <div className="space-y-2">
            {risk.gates.map((gate, i) => {
              const bgColor = {
                'PASS': 'bg-green-50',
                'BLOCK': 'bg-red-50',
                'WARN': 'bg-yellow-50',
              };
              const textColor = {
                'PASS': 'text-green-700',
                'BLOCK': 'text-red-700',
                'WARN': 'text-yellow-700',
              };
              const icon = {
                'PASS': <CheckCircle className="w-4 h-4" />,
                'BLOCK': <AlertCircle className="w-4 h-4" />,
                'WARN': <AlertCircle className="w-4 h-4" />,
              };

              return (
                <div key={i} className={`p-3 rounded ${bgColor[gate.status]}`}>
                  <div className="flex items-start gap-2">
                    <span className={`flex-shrink-0 ${textColor[gate.status]}`}>
                      {icon[gate.status]}
                    </span>
                    <div className="flex-1">
                      <p className={`font-medium ${textColor[gate.status]}`}>{gate.gate_name}</p>
                      <p className="text-sm text-gray-700">{gate.reason}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Critical Issues */}
        {risk.critical_issues.length > 0 && (
          <div>
            <h3 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" /> Critical Issues ({risk.critical_issues.length})
            </h3>
            <ul className="space-y-1">
              {risk.critical_issues.map((issue, i) => (
                <li key={i} className="text-sm text-red-700 flex gap-2">
                  <span>•</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {risk.warnings.length > 0 && (
          <div>
            <h3 className="font-semibold text-yellow-700 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> Warnings ({risk.warnings.length})
            </h3>
            <ul className="space-y-1">
              {risk.warnings.map((warning, i) => (
                <li key={i} className="text-sm text-yellow-700 flex gap-2">
                  <span>•</span>
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  // EXECUTION RESULTS TAB
  const renderExecutionTab = () => {
    const execution = pipelineData.execution_results;

    if (!execution) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-600">No execution results available yet.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-700">Total Duration</p>
            <p className="text-2xl font-bold text-blue-700">
              {execution.total_duration_ms ? (execution.total_duration_ms / 1000).toFixed(2) : '0'}s
            </p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm text-gray-700">Successful Steps</p>
            <p className="text-2xl font-bold text-green-700">
              {execution.step_results ? execution.step_results.filter(s => s.status === 'success').length : 0} / {execution.step_results?.length || 0}
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <p className="text-sm text-gray-700">Total Rows Retrieved</p>
            <p className="text-2xl font-bold text-purple-700">
              {execution.step_results ? execution.step_results.reduce((sum, s) => sum + s.rows, 0).toLocaleString() : 0}
            </p>
          </div>
        </div>

        {/* Steps */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Database className="w-5 h-5" /> Execution Steps
          </h3>
          <div className="space-y-2">
            {execution.step_results && execution.step_results.map((step) => {
              const isExpanded = expandedSteps.has(step.step);
              const statusIcon = {
                'success': <CheckCircle className="w-5 h-5 text-green-600" />,
                'failure': <AlertCircle className="w-5 h-5 text-red-600" />,
                'timeout': <AlertCircle className="w-5 h-5 text-orange-600" />,
                'skipped': <AlertCircle className="w-5 h-5 text-gray-600" />,
              };
              const statusBg = {
                'success': 'bg-green-50 border-green-200',
                'failure': 'bg-red-50 border-red-200',
                'timeout': 'bg-orange-50 border-orange-200',
                'skipped': 'bg-gray-50 border-gray-200',
              };

              return (
                <div key={step.step} className={`border rounded-lg p-4 ${statusBg[step.status]}`}>
                  <button
                    onClick={() => {
                      const newExpanded = new Set(expandedSteps);
                      if (isExpanded) {
                        newExpanded.delete(step.step);
                      } else {
                        newExpanded.add(step.step);
                      }
                      setExpandedSteps(newExpanded);
                    }}
                    className="w-full flex items-center justify-between hover:opacity-75"
                  >
                    <div className="flex items-center gap-3">
                      {statusIcon[step.status]}
                      <div className="text-left">
                        <p className="font-semibold text-gray-900">Step {step.step}</p>
                        <p className="text-sm text-gray-600">
                          {step.rows} rows • {step.duration_ms}ms
                        </p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    />
                  </button>

                  {isExpanded && (
                    <div className="mt-4 border-t pt-4 space-y-3">
                      {step.error && (
                        <div className="bg-red-100 text-red-700 p-3 rounded text-sm font-mono">
                          {step.error}
                        </div>
                      )}

                      {step.data.length > 0 && (
                        <div className="overflow-x-auto">
                          <table className="text-sm w-full">
                            <thead>
                              <tr className="border-b">
                                {step.columns.map((col) => (
                                  <th key={col} className="text-left px-2 py-1 font-medium">
                                    {col}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {step.data.slice(0, 10).map((row, i) => (
                                <tr key={i} className="border-b hover:bg-white hover:bg-opacity-50">
                                  {step.columns.map((col) => (
                                    <td key={`${i}-${col}`} className="px-2 py-1 text-gray-700">
                                      {String(row[col] ?? '').substring(0, 50)}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {step.data.length > 10 && (
                            <p className="text-gray-600 text-sm mt-2">
                              ... and {step.data.length - 10} more rows
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // INTERPRETATION TAB
  const renderInterpretationTab = () => {
    const interpretation = pipelineData.interpretation;

    if (!interpretation) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-600">No interpretation results available yet.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700 font-medium">{interpretation.summary}</p>
        </div>

        {/* Findings */}
        {interpretation.findings && interpretation.findings.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" /> Findings ({interpretation.findings.length})
            </h3>
            <div className="space-y-3">
              {interpretation.findings.map((finding, i) => {
                const severityColor = {
                  'CRITICAL': 'bg-red-50 border-red-200',
                  'HIGH': 'bg-orange-50 border-orange-200',
                  'MEDIUM': 'bg-yellow-50 border-yellow-200',
                  'LOW': 'bg-green-50 border-green-200',
                  'INFO': 'bg-blue-50 border-blue-200',
                };
                const severityTextColor = {
                  'CRITICAL': 'text-red-700',
                  'HIGH': 'text-orange-700',
                  'MEDIUM': 'text-yellow-700',
                  'LOW': 'text-green-700',
                  'INFO': 'text-blue-700',
                };

                return (
                  <div key={i} className={`p-4 border rounded-lg ${severityColor[finding.severity]}`}>
                    <div className="flex items-start gap-3">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${severityTextColor[finding.severity]}`}>
                        {finding.severity}
                      </span>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">{finding.title}</p>
                        <p className="text-sm text-gray-700 mt-1">{finding.description}</p>
                        {finding.affected_objects && (
                          <p className="text-xs text-gray-600 mt-2">
                            Affected: {finding.affected_objects.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Risk Observations */}
        {interpretation.risk_observations && interpretation.risk_observations.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" /> Risk Observations
            </h3>
            <ul className="space-y-1">
              {interpretation.risk_observations.map((obs, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span>•</span>
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {interpretation.recommendations && interpretation.recommendations.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Zap className="w-5 h-5" /> Recommendations
            </h3>
            <div className="space-y-2">
              {interpretation.recommendations.map((rec, i) => {
                const typeColor = {
                  'safe': 'bg-green-50 border-green-200',
                  'risky': 'bg-yellow-50 border-yellow-200',
                  'blocked': 'bg-red-50 border-red-200',
                };
                const typeBadge = {
                  'safe': 'bg-green-100 text-green-800',
                  'risky': 'bg-yellow-100 text-yellow-800',
                  'blocked': 'bg-red-100 text-red-800',
                };

                return (
                  <div key={i} className={`p-4 border rounded-lg ${typeColor[rec.type]}`}>
                    <div className="flex items-start gap-3">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${typeBadge[rec.type]}`}>
                        {rec.type.toUpperCase()}
                      </span>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900 font-medium">{rec.description}</p>
                        <div className="flex gap-2 mt-2 text-xs">
                          <span className="text-gray-600">Priority: {rec.priority}</span>
                          {rec.estimated_impact && (
                            <span className="text-gray-600">Impact: {rec.estimated_impact}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {interpretation.next_steps && (
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="font-semibold text-gray-900 mb-2">Next Steps</p>
            <p className="text-sm text-gray-700">{interpretation.next_steps}</p>
          </div>
        )}

        <div className="text-xs text-gray-500 pt-4 border-t">
          <p>Analysis by {interpretation.llm_model} • {interpretation.processing_time_ms ? (interpretation.processing_time_ms / 1000).toFixed(2) : '0'}s</p>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-screen overflow-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center justify-between border-b">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Play className="w-6 h-6" /> Playbook Execution
            </h1>
            <p className="text-blue-100 text-sm mt-1">{pipelineData.playbook}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium"
          >
            Close
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-gray-50">
          <button
            onClick={() => setActiveTab('risk')}
            className={`flex-1 px-6 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'risk'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📊 Risk Assessment
          </button>
          <button
            onClick={() => setActiveTab('execution')}
            className={`flex-1 px-6 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'execution'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            ⚙️ Execution Results
          </button>
          <button
            onClick={() => setActiveTab('interpretation')}
            className={`flex-1 px-6 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'interpretation'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🤖 Interpretation
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'risk' && renderRiskTab()}
          {activeTab === 'execution' && renderExecutionTab()}
          {activeTab === 'interpretation' && renderInterpretationTab()}
        </div>
      </div>
    </div>
  );
}
