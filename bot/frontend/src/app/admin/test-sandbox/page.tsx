'use client';

import { useState } from 'react';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService, { TestSandboxResponse } from '@/services/admin-config.service';
import { Play, Code, CheckCircle, XCircle, Copy, Clock, Zap, Hash, Brain, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';

export default function TestSandboxPage() {
  const [message, setMessage] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TestSandboxResponse | null>(null);

  const handleTest = async () => {
    if (!message.trim()) {
      toast.error('Vui lòng nhập message');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await adminConfigService.testSandbox({
        message,
        tenant_id: tenantId.trim() || undefined,
      });
      setResult(response);
      toast.success('Test thành công!');
    } catch (error: any) {
      toast.error(error.message || 'Test thất bại');
    } finally {
      setLoading(false);
    }
  };

  const copyTraceId = () => {
    if (result?.trace?.trace_id) {
      navigator.clipboard.writeText(result.trace.trace_id);
      toast.success('Trace ID đã được copy!');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ROUTED':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'META_HANDLED':
        return <MessageSquare className="h-5 w-5 text-blue-500" />;
      case 'UNKNOWN':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <XCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ROUTED':
        return 'text-green-600 dark:text-green-400';
      case 'META_HANDLED':
        return 'text-blue-600 dark:text-blue-400';
      case 'UNKNOWN':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'PATTERN':
        return <Hash className="h-4 w-4" />;
      case 'EMBEDDING':
        return <Brain className="h-4 w-4" />;
      case 'LLM':
        return <Zap className="h-4 w-4" />;
      case 'META':
        return <MessageSquare className="h-4 w-4" />;
      default:
        return <Code className="h-4 w-4" />;
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Test Sandbox</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Test routing với message và xem trace chi tiết
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Test Configuration
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Test Message *
              </label>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleTest()}
                placeholder="Nhập message để test routing..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tenant ID (Optional)
              </label>
              <input
                type="text"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                placeholder="UUID của tenant (để test tenant-specific configs)"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                disabled={loading}
              />
            </div>
            <button
              onClick={handleTest}
              disabled={loading || !message.trim()}
              className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-5 w-5 mr-2" />
              {loading ? 'Testing...' : 'Run Test'}
            </button>
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Routing Result */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Routing Result
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Domain</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {result.routing_result.domain || 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Intent</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {result.routing_result.intent || 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Confidence</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {result.routing_result.confidence !== undefined && result.routing_result.confidence !== null
                      ? `${(result.routing_result.confidence * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Source</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {result.routing_result.source}
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Status</div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(result.routing_result.status)}
                  <span className={`font-medium ${getStatusColor(result.routing_result.status)}`}>
                    {result.routing_result.status}
                  </span>
                </div>
              </div>
              {result.routing_result.intent_type && (
                <div className="mt-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Intent Type</div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {result.routing_result.intent_type}
                  </div>
                </div>
              )}
            </div>

            {/* Trace */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                  <Code className="h-5 w-5 mr-2" />
                  Execution Trace
                </h2>
                {result.trace.trace_id && (
                  <button
                    onClick={copyTraceId}
                    className="flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copy Trace ID
                  </button>
                )}
              </div>
              {result.trace.trace_id && (
                <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Trace ID</div>
                  <code className="text-sm text-gray-900 dark:text-white font-mono">
                    {result.trace.trace_id}
                  </code>
                </div>
              )}
              <div className="space-y-3">
                {result.trace.spans && result.trace.spans.length > 0 ? (
                  result.trace.spans.map((span: any, index: number) => (
                    <div
                      key={index}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <div className="font-medium text-gray-900 dark:text-white">
                            {span.step || `Step ${index + 1}`}
                          </div>
                          {span.decision_source && (
                            <div className="flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400">
                              {getSourceIcon(span.decision_source)}
                              <span className="bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                                {span.decision_source}
                              </span>
                            </div>
                          )}
                        </div>
                        {span.duration_ms !== undefined && (
                          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <Clock className="h-4 w-4 mr-1" />
                            {span.duration_ms}ms
                          </div>
                        )}
                      </div>
                      {span.score !== undefined && (
                        <div className="mb-2">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Confidence Score</div>
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                              <div
                                className="bg-primary-600 h-2 rounded-full"
                                style={{ width: `${(span.score * 100).toFixed(1)}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {(span.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      )}
                      {span.input && (
                        <details className="mt-2">
                          <summary className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-white">
                            View Input
                          </summary>
                          <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                            {JSON.stringify(span.input, null, 2)}
                          </pre>
                        </details>
                      )}
                      {span.output && (
                        <details className="mt-2">
                          <summary className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-white">
                            View Output
                          </summary>
                          <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                            {JSON.stringify(span.output, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No trace spans available
                  </div>
                )}
              </div>
            </div>

            {/* Configs Used */}
            {result.configs_used && result.configs_used.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Configs Used
                </h2>
                <div className="space-y-2">
                  {result.configs_used.map((config, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{config.step}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">{config.source}</div>
                      </div>
                      {config.score !== undefined && (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {config.score.toFixed(3)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

