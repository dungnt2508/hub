'use client';

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/shared/api/client';
import { ToolRequest } from '@/types';
import toast from 'react-hot-toast';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function ToolsPage() {
    const [tools, setTools] = useState<ToolRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [requestText, setRequestText] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const limit = 10;
    const previousToolsRef = useRef<ToolRequest[]>([]);

    useEffect(() => {
        fetchTools();
    }, [page]);

    // Polling for status updates
    useEffect(() => {
        const interval = setInterval(() => {
            // Only poll if there are pending/processing tools
            const hasPending = tools.some(t => t.status === 'pending' || t.status === 'processing');
            if (hasPending) {
                fetchTools(true); // Pass true to show notifications
            }
        }, 5000); // Poll every 5 seconds

        return () => clearInterval(interval);
    }, [tools.length]);

    const fetchTools = async (showNotification = false) => {
        try {
            setLoading(true);
            const res = await apiClient.get<{ tools: ToolRequest[] }>(`/tools?limit=${limit}&offset=${(page - 1) * limit}`);
            const fetchedTools = res.tools || [];
            
            // Check for status changes (for notifications)
            if (showNotification && previousToolsRef.current.length > 0) {
                fetchedTools.forEach((newTool: ToolRequest) => {
                    const oldTool = previousToolsRef.current.find(t => t.id === newTool.id);
                    if (oldTool && oldTool.status !== 'done' && newTool.status === 'done') {
                        toast.success(`Công cụ "${newTool.request_payload?.description?.substring(0, 50)}" đã hoàn thành!`, {
                            duration: 5000,
                        });
                    }
                });
            }
            
            previousToolsRef.current = fetchedTools;
            setTools(fetchedTools);
            setTotal(fetchedTools.length);
        } catch (err) {
            console.error('Failed to fetch tools', err);
            toast.error('Không thể tải danh sách công cụ');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!requestText) return;
        setSubmitting(true);
        try {
            await apiClient.post('/tools', {
                request_payload: { description: requestText }
            });
            setRequestText('');
            toast.success('Yêu cầu công cụ đã được gửi!');
            fetchTools();
        } catch (err: any) {
            // apiClient formats errors as ErrorResponse, so err.message is available directly
            toast.error(err.message || err.response?.data?.message || 'Lỗi khi gửi yêu cầu');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🛠️ Hộp thư công cụ</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Request Form */}
                <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 h-fit">
                    <h2 className="text-lg font-semibold mb-4">Yêu cầu công cụ mới</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                Mô tả công cụ bạn cần
                            </label>
                            <textarea
                                value={requestText}
                                onChange={(e) => setRequestText(e.target.value)}
                                placeholder="Ví dụ: Tôi cần một công cụ để đọc file PDF hóa đơn và trích xuất tổng tiền..."
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 h-32 resize-none"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                            {submitting ? 'Đang gửi...' : 'Gửi yêu cầu'}
                        </button>
                    </form>
                </div>

                {/* Requests List */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-lg font-semibold">Yêu cầu của bạn</h2>
                    {loading ? (
                        <div className="text-center py-12 text-gray-500">Đang tải...</div>
                    ) : tools.length === 0 ? (
                        <div className="text-center py-12 text-gray-500 bg-white dark:bg-gray-900 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                            Chưa có yêu cầu công cụ nào.
                        </div>
                    ) : (
                        <>
                            {tools.map((tool) => (
                                <div key={tool.id} className="bg-white dark:bg-gray-900 p-5 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
                                    <div className="flex justify-between items-start mb-3">
                                        <span className={`px-2 py-1 text-xs rounded-full ${tool.status === 'done' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                tool.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                                    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                            }`}>
                                            {tool.status.toUpperCase()}
                                        </span>
                                        <span className="text-xs text-gray-500">{new Date(tool.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-gray-800 dark:text-gray-200 mb-4">
                                        {tool.request_payload.description}
                                    </p>

                                    {tool.result && (
                                        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden relative group">
                                            <div className="absolute top-2 right-2 z-10 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => {
                                                        navigator.clipboard.writeText(JSON.stringify(tool.result, null, 2));
                                                        toast.success('Đã sao chép!');
                                                    }}
                                                    className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 shadow-lg"
                                                >
                                                    📋 Copy
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        const blob = new Blob([JSON.stringify(tool.result, null, 2)], { type: 'application/json' });
                                                        const url = URL.createObjectURL(blob);
                                                        const a = document.createElement('a');
                                                        a.href = url;
                                                        a.download = `tool-result-${tool.id}.json`;
                                                        a.click();
                                                        URL.revokeObjectURL(url);
                                                        toast.success('Đã tải xuống!');
                                                    }}
                                                    className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 shadow-lg"
                                                >
                                                    ⬇️ Download
                                                </button>
                                            </div>
                                            <SyntaxHighlighter
                                                language="json"
                                                style={vscDarkPlus}
                                                customStyle={{
                                                    margin: 0,
                                                    padding: '1rem',
                                                    borderRadius: '0.5rem',
                                                    fontSize: '0.875rem',
                                                }}
                                            >
                                                {JSON.stringify(tool.result, null, 2)}
                                            </SyntaxHighlighter>
                                        </div>
                                    )}
                                </div>
                            ))}
                            
                            {/* Pagination */}
                            {Math.ceil(total / limit) > 1 && (
                                <div className="flex items-center justify-center gap-2 pt-4">
                                    <button
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Trước
                                    </button>
                                    <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                                        Trang {page} / {Math.ceil(total / limit)}
                                    </span>
                                    <button
                                        onClick={() => setPage(p => Math.min(Math.ceil(total / limit), p + 1))}
                                        disabled={page >= Math.ceil(total / limit)}
                                        className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Sau
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
