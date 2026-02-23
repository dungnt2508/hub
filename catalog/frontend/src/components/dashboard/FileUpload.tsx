import { useState } from 'react';
import { summaryService } from '@/services/summary.service';

interface FileUploadProps {
    onSuccess: () => void;
}

export default function FileUpload({ onSuccess }: FileUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        setError('');

        try {
            await summaryService.processFile(file);
            setFile(null);
            // Reset file input
            const fileInput = document.getElementById('file-upload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

            onSuccess();
        } catch (err) {
            setError('Có lỗi xảy ra khi tải lên file.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700">
                    Tải lên File (PDF, DOCX, TXT)
                </label>
                <div className="mt-1 flex items-center">
                    <input
                        type="file"
                        name="file-upload"
                        id="file-upload"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading || !file}
                        className="ml-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                        {loading ? 'Đang tải...' : 'Tải lên'}
                    </button>
                </div>
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
        </form>
    );
}
