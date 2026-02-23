'use client';

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/shared/api/client';
import { Article } from '@/types';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function ArticlesPage() {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [url, setUrl] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const limit = 10;
    const previousArticlesRef = useRef<Article[]>([]);

    useEffect(() => {
        fetchArticles();
    }, [page]);

    // Polling for status updates
    useEffect(() => {
        const interval = setInterval(() => {
            // Only poll if there are pending/processing articles
            const hasPending = articles.some(a => a.status === 'pending' || a.status === 'processing');
            if (hasPending) {
                fetchArticles(true); // Pass true to show notifications
            }
        }, 5000); // Poll every 5 seconds

        return () => clearInterval(interval);
    }, [articles.length]); // Only depend on length to avoid infinite loop

    const fetchArticles = async (showNotification = false) => {
        try {
            setLoading(true);
            const res = await apiClient.get<{ articles: Article[] }>(`/articles?limit=${limit}&offset=${(page - 1) * limit}`);
            const fetchedArticles = res.articles || [];
            
            // Check for status changes (for notifications)
            if (showNotification && previousArticlesRef.current.length > 0) {
                fetchedArticles.forEach((newArticle: Article) => {
                    const oldArticle = previousArticlesRef.current.find(a => a.id === newArticle.id);
                    if (oldArticle && oldArticle.status !== 'done' && newArticle.status === 'done') {
                        toast.success(`Bài báo "${newArticle.title || newArticle.url?.substring(0, 50)}" đã được tóm tắt!`, {
                            duration: 5000,
                        });
                    }
                });
            }
            
            previousArticlesRef.current = fetchedArticles;
            setArticles(fetchedArticles);
            setTotal(fetchedArticles.length); // Backend should return total count
        } catch (err) {
            console.error('Failed to fetch articles', err);
            toast.error('Không thể tải danh sách bài báo');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url) return;
        setSubmitting(true);
        try {
            await apiClient.post('/articles', { url });
            setUrl('');
            toast.success('Bài báo đã được gửi để tóm tắt!');
            fetchArticles(); // Refresh list
        } catch (err: any) {
            toast.error(err.response?.data?.message || 'Lỗi khi gửi bài báo');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Bạn có chắc chắn muốn xóa?')) return;
        try {
            await apiClient.delete(`/articles/${id}`);
            setArticles(articles.filter(a => a.id !== id));
            toast.success('Đã xóa bài báo');
            // Refresh if current page becomes empty
            if (articles.length === 1 && page > 1) {
                setPage(page - 1);
            } else {
                fetchArticles();
            }
        } catch (err: any) {
            toast.error(err.response?.data?.message || 'Lỗi khi xóa');
        }
    };

    // Filter articles based on search and status
    const filteredArticles = articles.filter(article => {
        const matchesSearch = !searchQuery || 
            (article.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
             article.url?.toLowerCase().includes(searchQuery.toLowerCase()) ||
             article.summary?.toLowerCase().includes(searchQuery.toLowerCase()));
        const matchesStatus = statusFilter === 'all' || article.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">📰 Tóm tắt bài báo</h1>

                {/* Quick Add Form */}
                <form onSubmit={handleSubmit} className="flex gap-2 w-full md:w-auto">
                    <input
                        type="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Dán URL bài báo vào đây..."
                        className="flex-1 md:w-80 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                        required
                    />
                    <button
                        type="submit"
                        disabled={submitting}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
                    >
                        {submitting ? 'Đang xử lý...' : 'Tóm tắt'}
                    </button>
                </form>
            </div>

            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Tìm kiếm bài báo..."
                        className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                >
                    <option value="all">Tất cả trạng thái</option>
                    <option value="pending">Đang chờ</option>
                    <option value="processing">Đang xử lý</option>
                    <option value="done">Hoàn thành</option>
                    <option value="failed">Thất bại</option>
                </select>
            </div>

            {/* Articles List */}
            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="text-center py-12 text-gray-500">Đang tải danh sách bài báo...</div>
                ) : filteredArticles.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 bg-white dark:bg-gray-900 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                        {articles.length === 0 
                            ? 'Chưa có bài báo nào. Dán URL phía trên để bắt đầu!'
                            : 'Không tìm thấy bài báo nào phù hợp với bộ lọc.'}
                    </div>
                ) : (
                    filteredArticles.map((article) => (
                        <div key={article.id} className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 hover:border-blue-300 dark:hover:border-blue-700 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-1">
                                    {article.title || article.url}
                                </h3>
                                <span className={`px-2 py-1 text-xs rounded-full ${article.status === 'done' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                        article.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                    }`}>
                                    {article.status.toUpperCase()}
                                </span>
                            </div>

                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 line-clamp-2">
                                {article.summary || 'Đang chờ tóm tắt...'}
                            </p>

                            <div className="flex items-center justify-between text-sm">
                                <a href={article.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">
                                    Xem bài gốc
                                </a>
                                <div className="flex gap-3">
                                    {/* <button className="text-gray-500 hover:text-blue-500">🔄 Refetch</button> */}
                                    <button onClick={() => handleDelete(article.id)} className="text-red-500 hover:text-red-700">Xóa</button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Pagination */}
            {!loading && articles.length > 0 && totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Trước
                    </button>
                    <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                        Trang {page} / {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page >= totalPages}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Sau
                    </button>
                </div>
            )}
        </div>
    );
}
