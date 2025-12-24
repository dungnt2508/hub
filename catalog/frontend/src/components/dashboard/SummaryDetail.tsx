import { Article, Summary } from '@/services/summary.service';

interface SummaryDetailProps {
    article: Article;
    summary: Summary | null;
}

export default function SummaryDetail({ article, summary }: SummaryDetailProps) {
    return (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                    {article.title || 'Chi tiết bài viết'}
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    Nguồn: {article.source_value} ({article.source_type})
                </p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-1">
                    <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Tóm tắt</dt>
                        <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                            {summary?.summary_text || article.summary || 'Đang cập nhật...'}
                        </dd>
                    </div>

                    {summary?.insights_json && summary.insights_json.length > 0 && (
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Insights (Thông tin chi tiết)</dt>
                            <dd className="mt-1 text-sm text-gray-900">
                                <ul className="list-disc pl-5 space-y-1">
                                    {summary.insights_json.map((insight, index) => (
                                        <li key={index}>{insight}</li>
                                    ))}
                                </ul>
                            </dd>
                        </div>
                    )}

                    {summary?.data_points_json && summary.data_points_json.length > 0 && (
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Data Points (Số liệu quan trọng)</dt>
                            <dd className="mt-1 text-sm text-gray-900">
                                <ul className="list-disc pl-5 space-y-1">
                                    {summary.data_points_json.map((point, index) => (
                                        <li key={index}>{point}</li>
                                    ))}
                                </ul>
                            </dd>
                        </div>
                    )}
                </dl>
            </div>
        </div>
    );
}
