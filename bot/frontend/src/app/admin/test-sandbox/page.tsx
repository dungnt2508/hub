'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService, { TestSandboxResponse } from '@/services/admin-config.service';
import { Play, Code, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function TestSandboxPage() {
  const router = useRouter();
  const [message, setMessage] = useState('');
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
      const response = await adminConfigService.testSandbox({ message });
      setResult(response);
      toast.success('Test thành công!');
    } catch (error: any) {
      toast.error(error.message || 'Test thất bại');
    } finally {
      setLoading(false);
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
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Test Message
          </label>
          <div className="flex space-x-4">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleTest()}
              placeholder="Nhập message để test routing..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            />
            <button
              onClick={handleTest}
              disabled={loading}
              className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-5 w-5 mr-2" />
              {loading ? 'Testing...' : 'Test'}
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
                    {(result.routing_result.confidence * 100).toFixed(1)}%
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
                <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
                <div className="flex items-center space-x-2 mt-1">
                  {result.routing_result.status === 'success' ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="text-green-600 dark:text-green-400">Success</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 text-red-500" />
                      <span className="text-red-600 dark:text-red-400">{result.routing_result.status}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Trace */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Code className="h-5 w-5 mr-2" />
                Execution Trace
              </h2>
              <div className="space-y-3">
                {result.trace.spans.map((span, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-700/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium text-gray-900 dark:text-white">{span.step}</div>
                      {span.duration_ms && (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {span.duration_ms}ms
                        </div>
                      )}
                    </div>
                    {span.score !== undefined && (
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Score: {span.score.toFixed(3)}
                      </div>
                    )}
                    {span.decision_source && (
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Source: <code className="bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                          {span.decision_source}
                        </code>
                      </div>
                    )}
                    {span.output && (
                      <details className="mt-2">
                        <summary className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                          View Output
                        </summary>
                        <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                          {JSON.stringify(span.output, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
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

