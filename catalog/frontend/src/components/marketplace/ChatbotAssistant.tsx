'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Recommendation {
  productId: string;
  title: string;
  match: number;
  reason: string;
}

export default function ChatbotAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Xin chào 👋! Tôi là trợ lý tìm kiếm workflow. Bạn cần tự động hóa việc gì? Ví dụ: "Tôi cần automation email marketing" hoặc "Tôi muốn sync CRM sang Notion"',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickSuggestions = [
    'Email Marketing',
    'CRM Automation',
    'Social Media',
    'Data Sync',
  ];

  const handleSendMessage = async (text?: string) => {
    const messageText = text || input;
    if (!messageText.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Simulate API call to get recommendations
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Mock recommendations response
      const mockRecommendations: Recommendation[] = [
        {
          productId: '1',
          title: 'Email Marketing Automation',
          match: 95,
          reason: 'Hoàn hảo cho email campaign automation',
        },
        {
          productId: '2',
          title: 'CRM to Email Sync',
          match: 88,
          reason: 'Tự động gửi email dựa trên CRM data',
        },
        {
          productId: '3',
          title: 'Newsletter Auto-Sender',
          match: 82,
          reason: 'Schedule & auto-send newsletter hàng tuần',
        },
      ];

      setRecommendations(mockRecommendations);

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Dựa trên yêu cầu của bạn, tôi recommend 3 workflows tốt nhất:`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setShowRecommendations(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-gradient-to-br from-primary to-orange-600 text-white shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-300 flex items-center justify-center group animate-bounce hover:animate-none"
        >
          <MessageCircle className="h-6 w-6" />
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-white text-xs flex items-center justify-center font-bold">
            1
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-96 max-h-[600px] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200 dark:border-slate-700">
          {/* Header */}
          <div className="bg-gradient-to-r from-primary to-orange-600 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <MessageCircle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold">Trợ Lý Tìm Workflow</h3>
                <p className="text-xs text-white/80">AI-Powered Recommendations</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-slate-800/50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-primary text-white rounded-br-none'
                      : 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white rounded-bl-none border border-gray-200 dark:border-slate-600'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  <span
                    className={`text-xs mt-1 block ${
                      message.role === 'user'
                        ? 'text-white/70'
                        : 'text-gray-500 dark:text-slate-400'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString('vi-VN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            ))}

            {/* Recommendations Cards */}
            {showRecommendations && recommendations.length > 0 && (
              <div className="space-y-2">
                {recommendations.map((rec) => (
                  <a
                    key={rec.productId}
                    href={`/products/${rec.productId}`}
                    className="block p-3 bg-white dark:bg-slate-700 border border-primary/30 rounded-lg hover:border-primary hover:shadow-lg transition-all group cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-white text-sm group-hover:text-primary transition-colors">
                          {rec.title}
                        </h4>
                        <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">
                          {rec.reason}
                        </p>
                      </div>
                      <div className="ml-2 px-2 py-1 bg-primary/10 text-primary rounded text-xs font-bold">
                        {rec.match}%
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-center gap-2 text-gray-600 dark:text-slate-400">
                <Loader className="h-4 w-4 animate-spin" />
                <span className="text-sm">Đang tìm kiếm workflows...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          {!loading && messages.length <= 1 && (
            <div className="px-4 py-3 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800">
              <p className="text-xs text-gray-600 dark:text-slate-400 mb-2">
                Gợi ý nhanh:
              </p>
              <div className="flex flex-wrap gap-2">
                {quickSuggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSendMessage(suggestion)}
                    className="px-3 py-1.5 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-300 text-xs rounded-full transition-colors font-medium"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t border-gray-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-800">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !loading) {
                    handleSendMessage();
                  }
                }}
                placeholder="Nhu cầu của bạn..."
                className="flex-1 px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-900 dark:text-white rounded-lg border border-gray-300 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-primary placeholder:text-gray-500 dark:placeholder:text-slate-500 text-sm"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={loading || !input.trim()}
                className="p-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

