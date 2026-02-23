import { useEffect, useState } from 'react';
import { summaryService, Article } from '@/services/summary.service';
import Link from 'next/link';

interface SummaryListProps {
    refreshTrigger: number;
}

export default function SummaryList({ refreshTrigger }: SummaryListProps) {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSummaries = async () => {
            setLoading(true);
            try {
                const data = await summaryService.getSummaries();
                setArticles(data);
            } catch (error) {
                console.error('Failed to fetch summaries:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchSummaries();
    }, [refreshTrigger]);

    if (loading) {
        return <div className="text-center py-4">Đang tải danh sách...</div>;
    }

    if (articles.length === 0) {
        return <div className="text-center py-4 text-gray-500">Chưa có bài viết nào được tóm tắt.</div>;
    }

    return (
        <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Danh sách tóm tắt</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {articles.map((article) => (
                    <div key={article.id} className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200">
                        <div className="flex justify-between items-start mb-2">
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full 
                                ${article.source_type === 'url' ? 'bg-blue-100 text-blue-800' :
                                    article.source_type === 'rss' ? 'bg-green-100 text-green-800' :
                                        'bg-yellow-100 text-yellow-800'}`}>
                                {article.source_type.toUpperCase()}
                            </span>
                            <span className="text-xs text-gray-500">
                                {new Date(article.created_at).toLocaleDateString('vi-VN')}
                            </span>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2 line-clamp-2" title={article.title}>
                            {article.title || 'Không có tiêu đề'}
                        </h3>
                        <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                            {article.summary || 'Đang xử lý...'}
                        </p>
                        <Link
                            href={`/dashboard/summaries/${article.id}`}
                            className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                        >
                            Xem chi tiết &rarr;
                        </Link>
                    </div>
                ))}
            </div>
        </div>
    );
}
