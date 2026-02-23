import { useState } from 'react';
import { summaryService } from '@/services/summary.service';

interface UrlInputProps {
    onSuccess: () => void;
}

export default function UrlInput({ onSuccess }: UrlInputProps) {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await summaryService.processUrl(url);
            setUrl('');
            onSuccess();
        } catch (err) {
            setError('Có lỗi xảy ra khi xử lý URL.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                    URL Bài viết
                </label>
                <div className="mt-1 flex rounded-md shadow-sm">
                    <input
                        type="url"
                        name="url"
                        id="url"
                        className="flex-1 block w-full rounded-none rounded-l-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                        placeholder="https://example.com/bai-viet"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {loading ? 'Đang xử lý...' : 'Tóm tắt'}
                    </button>
                </div>
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
        </form>
    );
}
