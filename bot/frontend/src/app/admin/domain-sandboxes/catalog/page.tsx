'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/AdminLayout';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  MessageSquare,
  Zap,
  Brain,
  Search,
  Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/shared/api/client';

/**
 * Catalog Domain Sandbox - Test Intent Classification & Hybrid Search
 * 
 * Purpose: Frontend UI to test catalog domain components
 * - Test intent classification
 * - Test hybrid search routing
 * - See retrieval strategy selection
 * - Debug intent classification results
 */

interface IntentClassificationResult {
  intent_type: 'PRODUCT_SEARCH' | 'PRODUCT_SPECIFIC_INFO' | 'PRODUCT_COMPARISON' | 'PRODUCT_COUNT';
  confidence: number;
  reason: string;
  extracted_info: Record<string, any>;
}

interface CatalogQueryResponse {
  answer: string;
  intent_type: string;
  retrieval_method: 'vector_search' | 'hybrid_search' | 'db_query' | 'db_count';
  products_found: number;
  confidence: number;
  classification: IntentClassificationResult;
  sources?: Array<{
    title: string;
    excerpt?: string;
  }>;
}

export default function CatalogSandboxPage() {
  // ============================================================
  // STATE
  // ============================================================
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CatalogQueryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'input' | 'classification' | 'results'>('input');

  // Sample queries for quick testing
  const sampleQueries = [
    { query: 'Công cụ AI nào tốt nhất?', label: 'Generic Search' },
    { query: 'Giá của ChatGPT bao nhiêu?', label: 'Price Query' },
    { query: 'Tính năng nào của Claude?', label: 'Features Query' },
    { query: 'So sánh ChatGPT và Gemini', label: 'Comparison' },
    { query: 'Có bao nhiêu công cụ miễn phí?', label: 'Count Query' },
  ];

  // ============================================================
  // API CALLS
  // ============================================================
  const handleTestQuery = async () => {
    if (!query.trim()) {
      toast.error('Vui lòng nhập câu hỏi');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // Call backend endpoint
      const response = await apiClient.post<CatalogQueryResponse>(
        '/api/catalog/query',
        { question: query }
      );
      
      setResult(response);
      setActiveTab('classification');
      toast.success('Query processed successfully');
    } catch (error: any) {
      toast.error(error.message || 'Failed to process query');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery);
    // Auto-run after setting query
    setTimeout(() => {
      setQuery(sampleQuery);
    }, 0);
  };

  // ============================================================
  // RENDER FUNCTIONS
  // ============================================================

  const renderIntentBadge = (intentType: string) => {
    const colors: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
      PRODUCT_SEARCH: {
        bg: 'bg-blue-100 dark:bg-blue-900/30',
        text: 'text-blue-800 dark:text-blue-200',
        icon: <Search className="h-3 w-3" />,
      },
      PRODUCT_SPECIFIC_INFO: {
        bg: 'bg-purple-100 dark:bg-purple-900/30',
        text: 'text-purple-800 dark:text-purple-200',
        icon: <Filter className="h-3 w-3" />,
      },
      PRODUCT_COMPARISON: {
        bg: 'bg-green-100 dark:bg-green-900/30',
        text: 'text-green-800 dark:text-green-200',
        icon: <Zap className="h-3 w-3" />,
      },
      PRODUCT_COUNT: {
        bg: 'bg-orange-100 dark:bg-orange-900/30',
        text: 'text-orange-800 dark:text-orange-200',
        icon: <AlertCircle className="h-3 w-3" />,
      },
    };

    const style = colors[intentType] || colors.PRODUCT_SEARCH;

    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${style.bg}`}>
        <span className={style.text}>{style.icon}</span>
        <span className={`text-xs font-semibold ${style.text}`}>{intentType}</span>
      </div>
    );
  };

  const renderRetrievalMethodBadge = (method: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      vector_search: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-800 dark:text-cyan-200' },
      hybrid_search: { bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-800 dark:text-indigo-200' },
      db_query: { bg: 'bg-teal-100 dark:bg-teal-900/30', text: 'text-teal-800 dark:text-teal-200' },
      db_count: { bg: 'bg-rose-100 dark:bg-rose-900/30', text: 'text-rose-800 dark:text-rose-200' },
    };

    const style = colors[method] || colors.vector_search;

    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${style.bg} ${style.text} text-xs font-mono`}>
        {method}
      </div>
    );
  };

  const renderClassificationDetails = () => {
    if (!result || !result.classification) return null;

    const classification = result.classification;

    return (
      <div className="space-y-4">
        {/* Main Classification Result */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Brain className="h-5 w-5 mr-2" />
            Intent Classification Result
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Intent Type</div>
              {renderIntentBadge(classification.intent_type)}
            </div>

            <div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Confidence</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${classification.confidence * 100}%` }}
                  />
                </div>
                <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white">
                  {(classification.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            <div className="col-span-2">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Classification Reason</div>
              <p className="text-sm text-gray-700 dark:text-gray-300 italic">{classification.reason}</p>
            </div>
          </div>
        </div>

        {/* Extracted Information */}
        {Object.keys(classification.extracted_info).length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Extracted Information</h4>
            <div className="space-y-2">
              {Object.entries(classification.extracted_info).map(([key, value]) => (
                <div key={key} className="flex items-start justify-between p-2 bg-white dark:bg-gray-800 rounded">
                  <span className="text-xs font-mono text-gray-600 dark:text-gray-400">{key}</span>
                  <span className="text-sm text-gray-900 dark:text-white font-medium">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Retrieval Strategy */}
        <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
            <Zap className="h-4 w-4 mr-2" />
            Retrieval Strategy Selected
          </h4>
          <div className="flex items-center gap-2">
            {renderRetrievalMethodBadge(result.retrieval_method)}
            <span className="text-xs text-gray-600 dark:text-gray-400 ml-2">
              Based on intent classification
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    if (!result) return null;

    return (
      <div className="space-y-4">
        {/* Final Answer */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <MessageSquare className="h-5 w-5 mr-2" />
            Bot Answer
          </h3>
          <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
            <p className="text-gray-900 dark:text-white leading-relaxed">{result.answer}</p>
          </div>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Products Found</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{result.products_found}</div>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Answer Confidence</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${result.confidence * 100}%` }}
                />
              </div>
              <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white">
                {(result.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Sources */}
        {result.sources && result.sources.length > 0 && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Sources</h3>
            <div className="space-y-3">
              {result.sources.map((source, idx) => (
                <div key={idx} className="border-l-2 border-blue-500 pl-4">
                  <div className="font-medium text-gray-900 dark:text-white">{source.title}</div>
                  {source.excerpt && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{source.excerpt}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ============================================================
  // MAIN RENDER
  // ============================================================
  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Catalog Domain Sandbox
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Test intent classification, hybrid search, and answer generation
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab('input')}
              className={`pb-3 px-1 font-medium text-sm transition ${
                activeTab === 'input'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Input Query
            </button>
            {result && (
              <>
                <button
                  onClick={() => setActiveTab('classification')}
                  className={`pb-3 px-1 font-medium text-sm transition ${
                    activeTab === 'classification'
                      ? 'border-b-2 border-blue-600 text-blue-600'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  Intent Classification
                </button>
                <button
                  onClick={() => setActiveTab('results')}
                  className={`pb-3 px-1 font-medium text-sm transition ${
                    activeTab === 'results'
                      ? 'border-b-2 border-blue-600 text-blue-600'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  Results
                </button>
              </>
            )}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'input' && (
          <div className="space-y-4">
            {/* Query Input */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Test Query
              </h2>

              <div className="space-y-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      handleTestQuery();
                    }
                  }}
                  placeholder="Nhập câu hỏi về sản phẩm..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                  rows={4}
                />

                <button
                  onClick={handleTestQuery}
                  disabled={loading || !query.trim()}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
                >
                  {loading ? 'Processing...' : 'Process Query'}
                </button>
              </div>
            </div>

            {/* Sample Queries */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Sample Queries
              </h2>

              <div className="grid grid-cols-1 gap-2">
                {sampleQueries.map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(sample.query);
                      // Trigger query after state update
                      setTimeout(() => {
                        setQuery(sample.query);
                      }, 100);
                    }}
                    className="text-left px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
                  >
                    <div className="font-medium text-gray-900 dark:text-white text-sm">
                      {sample.label}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      "{sample.query}"
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'classification' && result && renderClassificationDetails()}

        {activeTab === 'results' && result && renderResults()}
      </div>
    </AdminLayout>
  );
}

