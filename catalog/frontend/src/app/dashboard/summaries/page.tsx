'use client';

import { useState } from 'react';
import UrlInput from '@/components/dashboard/UrlInput';
import RssInput from '@/components/dashboard/RssInput';
import FileUpload from '@/components/dashboard/FileUpload';
import SummaryList from '@/components/dashboard/SummaryList';

export default function SummariesPage() {
    const [activeTab, setActiveTab] = useState<'url' | 'rss' | 'file'>('url');
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const handleSuccess = () => {
        setRefreshTrigger((prev) => prev + 1);
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Quản lý Tóm tắt Đa nguồn</h1>

            <div className="bg-white shadow rounded-lg p-6 mb-8">
                <div className="border-b border-gray-200 mb-4">
                    <nav className="-mb-px flex space-x-8">
                        <button
                            onClick={() => setActiveTab('url')}
                            className={`${activeTab === 'url'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Thêm URL
                        </button>
                        <button
                            onClick={() => setActiveTab('rss')}
                            className={`${activeTab === 'rss'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Thêm RSS
                        </button>
                        <button
                            onClick={() => setActiveTab('file')}
                            className={`${activeTab === 'file'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Tải File
                        </button>
                    </nav>
                </div>

                <div className="mt-4">
                    {activeTab === 'url' && <UrlInput onSuccess={handleSuccess} />}
                    {activeTab === 'rss' && <RssInput onSuccess={handleSuccess} />}
                    {activeTab === 'file' && <FileUpload onSuccess={handleSuccess} />}
                </div>
            </div>

            <SummaryList refreshTrigger={refreshTrigger} />
        </div>
    );
}
