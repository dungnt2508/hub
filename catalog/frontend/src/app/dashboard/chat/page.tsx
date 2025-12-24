'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
// Note: chat page uses fetch directly for streaming, no apiClient needed
import toast from 'react-hot-toast';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function ChatPage() {
    const { user } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Load message history from localStorage
    useEffect(() => {
        const saved = localStorage.getItem(`chat-history-${user?.userId}`);
        if (saved) {
            try {
                setMessages(JSON.parse(saved));
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }
    }, [user?.userId]);

    // Save messages to localStorage
    useEffect(() => {
        if (messages.length > 0 && user?.userId) {
            localStorage.setItem(`chat-history-${user?.userId}`, JSON.stringify(messages));
        }
    }, [messages, user?.userId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Prepare messages for API (include history if needed, here just sending all)
            const apiMessages = [...messages, userMessage].map(m => ({
                role: m.role,
                content: m.content
            }));

            // Use fetch directly for streaming support (axios streaming is trickier)
            const token = localStorage.getItem('token');
            
            if (!token) {
                throw new Error('Bạn cần đăng nhập để sử dụng tính năng chat');
            }
            
            // Create abort controller for cleanup
            abortControllerRef.current = new AbortController();
            
            const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api'}/chat`;
            console.log('Sending chat request to:', apiUrl);
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    messages: apiMessages,
                    stream: true,
                }),
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                // Try to get error message from response
                let errorMessage = `Chat failed (${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch (e) {
                    // If response is not JSON, use status text
                    errorMessage = response.statusText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            if (!response.body) throw new Error('No response body');

            // Create a placeholder for the assistant's response
            setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6);
                            if (dataStr === '[DONE]') break;

                            try {
                                const data = JSON.parse(dataStr);
                                
                                // Check for error in SSE data
                                if (data.error) {
                                    throw new Error(data.error);
                                }
                                
                                if (data.content) {
                                    assistantMessage += data.content;

                                    // Update the last message (assistant's) with new content
                                    setMessages((prev) => {
                                        const newMessages = [...prev];
                                        const lastMsg = newMessages[newMessages.length - 1];
                                        if (lastMsg.role === 'assistant') {
                                            lastMsg.content = assistantMessage;
                                        }
                                        return newMessages;
                                    });
                                }
                            } catch (e) {
                                console.error('Error parsing SSE data', e);
                                // If it's an error from backend, throw it
                                if (e instanceof Error && e.message) {
                                    throw e;
                                }
                            }
                        }
                    }
                }
            } catch (readError) {
                if (readError instanceof Error && readError.name === 'AbortError') {
                    console.log('Chat stream aborted');
                    return;
                }
                throw readError;
            }
        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log('Chat request aborted');
                return;
            }
            console.error('Chat error:', error);
            
            // Get error message with more details
            let errorMessage = 'Lỗi kết nối. Vui lòng thử lại.';
            
            if (error.message) {
                errorMessage = error.message;
            } else if (error.name === 'TypeError' && error.message?.includes('fetch')) {
                errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra xem backend có đang chạy không.';
            } else if (error.message?.includes('Failed to fetch')) {
                errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra:\n- Backend có đang chạy không (http://localhost:3001)\n- CORS đã được cấu hình đúng chưa';
            }
            
            setMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === 'assistant' && !lastMsg.content) {
                    lastMsg.content = `⚠️ ${errorMessage}`;
                } else {
                    newMessages.push({ role: 'assistant', content: `⚠️ ${errorMessage}` });
                }
                return newMessages;
            });
            
            // Show toast notification
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleClearChat = () => {
        if (window.confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử trò chuyện?')) {
            setMessages([]);
            if (user?.userId) {
                localStorage.removeItem(`chat-history-${user.userId}`);
            }
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">💬 Trò chuyện với Bot</h1>
                <div className="flex items-center gap-3">
                    {messages.length > 0 && (
                        <button
                            onClick={handleClearChat}
                            className="text-sm text-gray-500 hover:text-red-600 dark:hover:text-red-400 px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                        >
                            🗑️ Xóa lịch sử
                        </button>
                    )}
                    <div className="text-sm text-gray-500 bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full">
                        Persona đang dùng: <span className="font-semibold text-blue-600">Mặc định</span>
                    </div>
                </div>
            </div>

            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <div className="text-4xl mb-2">👋</div>
                        <p>Bắt đầu trò chuyện để xem sức mạnh của Persona!</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-none'
                                }`}
                        >
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>
                    </div>
                ))}

                {isLoading && messages[messages.length - 1]?.role === 'user' && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3 rounded-bl-none flex gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="mt-4">
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Nhập tin nhắn..."
                        className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        Gửi
                    </button>
                </form>
            </div>
        </div>
    );
}
