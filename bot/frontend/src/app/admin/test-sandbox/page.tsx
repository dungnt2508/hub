'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService, { TestSandboxResponse } from '@/services/admin-config.service';
import { 
  Play, Code, CheckCircle, XCircle, Copy, Clock, Zap, Hash, Brain, MessageSquare,
  RotateCcw, Database, Activity, AlertCircle, CheckCircle2, XCircle2, Loader2,
  ChevronRight, ChevronDown, RefreshCw, Trash2, FileText, Settings
} from 'lucide-react';
import toast from 'react-hot-toast';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  trace_id?: string;
  session_id?: string;
}

interface TestScenario {
  id: string;
  name: string;
  description: string;
  messages: string[];
  expectedDomain?: string;
  expectedIntent?: string;
}

const TEST_SCENARIOS: TestScenario[] = [
  {
    id: 'leave-request-flow',
    name: 'Leave Request Flow (Multi-turn)',
    description: 'Test complete leave request với slot accumulation',
    messages: [
      'Tôi muốn xin nghỉ phép',
      'từ ngày mai',
      'đến ngày 2025-02-05',
      'nghỉ phép gia đình'
    ],
    expectedDomain: 'hr',
    expectedIntent: 'create_leave_request'
  },
  {
    id: 'continuation-flow',
    name: 'Continuation Flow',
    description: 'Test continuation với slot value detection',
    messages: [
      'Tôi muốn xin nghỉ phép',
      'mai'  // Should trigger CONTINUATION
    ],
    expectedDomain: 'hr',
    expectedIntent: 'create_leave_request'
  },
  {
    id: 'unknown-recovery',
    name: 'UNKNOWN Recovery',
    description: 'Test UNKNOWN với disambiguation',
    messages: [
      'xyz abc 123'  // Should return UNKNOWN with options
    ]
  },
  {
    id: 'cross-domain',
    name: 'Cross-Domain Conversation',
    description: 'Test switching giữa domains với context boost',
    messages: [
      'Tôi còn bao nhiêu ngày phép?',  // HR
      'Tìm kiếm sản phẩm',  // Catalog
      'Thông tin về nghỉ phép'  // Should boost HR
    ]
  },
  {
    id: 'slot-validation',
    name: 'Slot Validation',
    description: 'Test slot format validation',
    messages: [
      'Tôi muốn xin nghỉ phép từ ngày 32/13/2025'  // Invalid date
    ]
  }
];

export default function TestSandboxPage() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TestSandboxResponse | null>(null);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [scenarioStep, setScenarioStep] = useState(0);
  const [showSessionState, setShowSessionState] = useState(true);
  const [showTrace, setShowTrace] = useState(true);
  const [showDomainResponse, setShowDomainResponse] = useState(true);

  // Load session_id from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('test_sandbox_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  // Save session_id to localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('test_sandbox_session_id', sessionId);
    } else {
      localStorage.removeItem('test_sandbox_session_id');
    }
  }, [sessionId]);

  const handleTest = async (testMessage?: string) => {
    const messageToSend = testMessage || message;
    if (!messageToSend.trim()) {
      toast.error('Vui lòng nhập message');
      return;
    }

    setLoading(true);
    setResult(null);

    // Add user message to conversation
    const userMessage: ConversationMessage = {
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
    };
    setConversation(prev => [...prev, userMessage]);

    try {
      const response = await adminConfigService.testSandbox({
        message: messageToSend,
        tenant_id: tenantId.trim() || undefined,
        session_id: sessionId || undefined,
      });
      
      // Update session_id for next turn
      if (response.session_id) {
        setSessionId(response.session_id);
      }
      
      // Add assistant response to conversation
      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: response.domain_response?.message || response.routing_result.message || 'No response',
        timestamp: new Date(),
        trace_id: response.trace.trace_id,
        session_id: response.session_id || undefined,
      };
      setConversation(prev => [...prev, assistantMessage]);
      
      setResult(response);
      
      // Show toast based on result
      if (response.routing_result.status === 'UNKNOWN') {
        toast.error('Không tìm thấy domain phù hợp', {
          icon: '❓',
        });
      } else if (response.routing_result.status === 'ROUTED') {
        toast.success(`Routed to ${response.routing_result.domain}`, {
          icon: '✅',
        });
      } else if (response.routing_result.status === 'META_HANDLED') {
        toast.success('Meta task handled', {
          icon: 'ℹ️',
        });
      }
    } catch (error: any) {
      toast.error(error.message || 'Test thất bại');
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: `Error: ${error.message || 'Test failed'}`,
        timestamp: new Date(),
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioSelect = (scenarioId: string) => {
    const scenario = TEST_SCENARIOS.find(s => s.id === scenarioId);
    if (!scenario) return;
    
    setSelectedScenario(scenarioId);
    setScenarioStep(0);
    setSessionId(null);  // Reset session for new scenario
    setConversation([]);
    setResult(null);
    setMessage(scenario.messages[0]);
  };

  const handleScenarioNext = () => {
    if (!selectedScenario) return;
    const scenario = TEST_SCENARIOS.find(s => s.id === selectedScenario);
    if (!scenario) return;
    
    if (scenarioStep < scenario.messages.length - 1) {
      const nextStep = scenarioStep + 1;
      setScenarioStep(nextStep);
      setMessage(scenario.messages[nextStep]);
      // Auto-send next message
      setTimeout(() => {
        handleTest(scenario.messages[nextStep]);
      }, 500);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setConversation([]);
    setResult(null);
    setMessage('');
    setSelectedScenario(null);
    setScenarioStep(0);
    toast.success('Đã reset conversation');
  };

  const copyTraceId = () => {
    if (result?.trace?.trace_id) {
      navigator.clipboard.writeText(result.trace.trace_id);
      toast.success('Trace ID đã được copy!');
    }
  };

  const copySessionId = () => {
    if (sessionId) {
      navigator.clipboard.writeText(sessionId);
      toast.success('Session ID đã được copy!');
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
      case 'CONTINUATION':
        return <RotateCcw className="h-4 w-4" />;
      case 'ESCALATION':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Code className="h-4 w-4" />;
    }
  };

  const getConversationStateColor = (state?: string) => {
    switch (state) {
      case 'idle':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
      case 'routing':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
      case 'processing':
        return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200';
      case 'need_info':
        return 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200';
      case 'complete':
        return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
      case 'error':
        return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Test Sandbox - Full Flow Testing</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Test toàn bộ flow từ đầu đến cuối: Router → Domain → Session Persistence
            </p>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </button>
        </div>

        {/* Test Scenarios */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            Test Scenarios
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {TEST_SCENARIOS.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => handleScenarioSelect(scenario.id)}
                className={`p-4 text-left border-2 rounded-lg transition-all ${
                  selectedScenario === scenario.id
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                }`}
              >
                <div className="font-semibold text-gray-900 dark:text-white mb-1">
                  {scenario.name}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {scenario.description}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  {scenario.messages.length} messages
                </div>
              </button>
            ))}
          </div>
          {selectedScenario && (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Scenario Progress: {scenarioStep + 1} / {TEST_SCENARIOS.find(s => s.id === selectedScenario)?.messages.length}
                </div>
                {scenarioStep < (TEST_SCENARIOS.find(s => s.id === selectedScenario)?.messages.length || 0) - 1 && (
                  <button
                    onClick={handleScenarioNext}
                    disabled={loading}
                    className="flex items-center px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                  >
                    Next Step
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </button>
                )}
              </div>
              <div className="flex space-x-2">
                {TEST_SCENARIOS.find(s => s.id === selectedScenario)?.messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex-1 h-2 rounded ${
                      idx <= scenarioStep
                        ? 'bg-primary-600'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Conversation Chat Interface */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <MessageSquare className="h-5 w-5 mr-2" />
            Conversation
            {sessionId && (
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                Session: {sessionId.substring(0, 8)}...
              </span>
            )}
          </h2>
          
          {/* Conversation History */}
          <div className="mb-4 h-64 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-900/50">
            {conversation.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                No messages yet. Start a conversation or select a test scenario.
              </div>
            ) : (
              <div className="space-y-4">
                {conversation.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="text-sm">{msg.content}</div>
                      <div className={`text-xs mt-1 ${
                        msg.role === 'user' ? 'text-primary-100' : 'text-gray-500 dark:text-gray-400'
                      }`}>
                        {msg.timestamp.toLocaleTimeString()}
                        {msg.trace_id && (
                          <span className="ml-2">Trace: {msg.trace_id.substring(0, 8)}...</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input Section */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Message
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !loading && handleTest()}
                  placeholder="Nhập message để test..."
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  disabled={loading}
                />
                <button
                  onClick={() => handleTest()}
                  disabled={loading || !message.trim()}
                  className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Play className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tenant ID (Optional)
              </label>
              <input
                type="text"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                placeholder="UUID của tenant"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className="space-y-6">
            {/* Routing Result */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                Routing Result
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
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
                  <div className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                    {getSourceIcon(result.routing_result.source)}
                    <span className="ml-2">{result.routing_result.source}</span>
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
              {result.routing_result.options && result.routing_result.options.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Disambiguation Options</div>
                  <div className="flex flex-wrap gap-2">
                    {result.routing_result.options.map((option, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-200 rounded-lg text-sm"
                      >
                        {option}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Session State */}
            {result.session_state && showSessionState && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <Database className="h-5 w-5 mr-2" />
                    Session State
                  </h2>
                  <div className="flex items-center space-x-2">
                    {sessionId && (
                      <button
                        onClick={copySessionId}
                        className="flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                      >
                        <Copy className="h-4 w-4 mr-1" />
                        Copy Session ID
                      </button>
                    )}
                    <button
                      onClick={() => setShowSessionState(!showSessionState)}
                      className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                      {showSessionState ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                {showSessionState && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Conversation State</div>
                        <div className={`px-2 py-1 rounded text-sm font-medium ${getConversationStateColor(result.session_state.conversation_state)}`}>
                          {result.session_state.conversation_state || 'idle'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Active Domain</div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {result.session_state.active_domain || 'None'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Last Domain</div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {result.session_state.last_domain || 'None'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Pending Intent</div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {result.session_state.pending_intent || 'None'}
                        </div>
                      </div>
                    </div>
                    {result.session_state.missing_slots && result.session_state.missing_slots.length > 0 && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Missing Slots</div>
                        <div className="flex flex-wrap gap-2">
                          {result.session_state.missing_slots.map((slot, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200 rounded text-xs"
                            >
                              {slot}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {result.session_state.slots_memory && Object.keys(result.session_state.slots_memory).length > 0 && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Slots Memory</div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <pre className="text-xs text-gray-900 dark:text-white overflow-x-auto">
                            {JSON.stringify(result.session_state.slots_memory, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Retry Count:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                          {result.session_state.retry_count || 0}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Escalation:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                          {result.session_state.escalation_flag ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Domain Response */}
            {result.domain_response && showDomainResponse && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <CheckCircle2 className="h-5 w-5 mr-2" />
                    Domain Response
                  </h2>
                  <button
                    onClick={() => setShowDomainResponse(!showDomainResponse)}
                    className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  >
                    {showDomainResponse ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                  </button>
                </div>
                {showDomainResponse && (
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Status</div>
                      <div className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium ${
                        result.domain_response.status === 'SUCCESS'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                          : result.domain_response.status === 'NEED_MORE_INFO'
                          ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                      }`}>
                        {result.domain_response.status}
                      </div>
                    </div>
                    {result.domain_response.message && (
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Message</div>
                        <div className="text-gray-900 dark:text-white">{result.domain_response.message}</div>
                      </div>
                    )}
                    {result.domain_response.next_action && (
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Next Action</div>
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded text-sm">
                            {result.domain_response.next_action}
                          </span>
                          {result.domain_response.next_action_params && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {JSON.stringify(result.domain_response.next_action_params)}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                    {result.domain_response.missing_slots && result.domain_response.missing_slots.length > 0 && (
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Missing Slots</div>
                        <div className="flex flex-wrap gap-2">
                          {result.domain_response.missing_slots.map((slot, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200 rounded text-xs"
                            >
                              {slot}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {result.domain_response.data && (
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Data</div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <pre className="text-xs text-gray-900 dark:text-white overflow-x-auto">
                            {JSON.stringify(result.domain_response.data, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Trace */}
            {showTrace && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <Code className="h-5 w-5 mr-2" />
                    Execution Trace
                  </h2>
                  <div className="flex items-center space-x-2">
                    {result.trace.trace_id && (
                      <button
                        onClick={copyTraceId}
                        className="flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                      >
                        <Copy className="h-4 w-4 mr-1" />
                        Copy Trace ID
                      </button>
                    )}
                    <button
                      onClick={() => setShowTrace(!showTrace)}
                      className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                      {showTrace ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                {showTrace && (
                  <>
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
                  </>
                )}
              </div>
            )}

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
