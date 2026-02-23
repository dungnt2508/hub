'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { summaryService, Article, Summary } from '@/services/summary.service';
import SummaryDetail from '@/components/dashboard/SummaryDetail';

export default function SummaryDetailPage() {
    const params = useParams();
    const router = useRouter();
    const id = params.id as string;

    const [article, setArticle] = useState<Article | null>(null);
    const [summary, setSummary] = useState<Summary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!id) return;

        const fetchDetail = async () => {
            setLoading(true);
            try {
                const data = await summaryService.getSummary(id);
                setArticle(data.article);
                setSummary(data.summary);
            } catch (err) {
                console.error('Failed to fetch summary details:', err);
                setError('Không thể tải chi tiết bài viết.');
            } finally {
                setLoading(false);
            }
        };

        fetchDetail();
    }, [id]);

    if (loading) {
        return <div className="text-center py-8">Đang tải chi tiết...</div>;
    }

    if (error || !article) {
        return (
            <div className="text-center py-8">
                <p className="text-red-500 mb-4">{error || 'Bài viết không tồn tại.'}</p>
                <button
                    onClick={() => router.back()}
                    className="text-indigo-600 hover:text-indigo-800"
                >
                    &larr; Quay lại
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-6">
                <button
                    onClick={() => router.back()}
                    className="text-indigo-600 hover:text-indigo-800 flex items-center"
                >
                    &larr; Quay lại danh sách
                </button>
            </div>
            <SummaryDetail article={article} summary={summary} />
        </div>
    );
}
