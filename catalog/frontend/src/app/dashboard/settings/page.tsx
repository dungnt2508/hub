'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
// import PersonaSettings from '@/components/PersonaSettings'; // Ẩn tạm thời, tập trung vào marketplace mini

export default function SettingsPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { user } = useAuth();

    const [activeTab, setActiveTab] = useState('profile');

    useEffect(() => {
        const tab = searchParams.get('tab');
        if (tab && ['profile', 'general'].includes(tab)) {
            setActiveTab(tab);
        }
    }, [searchParams]);

    const handleTabChange = (tab: string) => {
        setActiveTab(tab);
        router.push(`/dashboard/settings?tab=${tab}`);
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">⚙️ Cài đặt</h1>

            {/* Tabs Navigation */}
            <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => handleTabChange('profile')}
                        className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'profile'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                            }`}
                    >
                        👤 Tài khoản
                    </button>
                    {/* Bot tab - Ẩn tạm thời, tập trung vào marketplace mini */}
                    {/* <button
                        onClick={() => handleTabChange('bot')}
                        className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'bot'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                            }`}
                    >
                        🤖 Cấu hình Bot (Persona)
                    </button> */}
                    <button
                        onClick={() => handleTabChange('general')}
                        className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'general'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                            }`}
                    >
                        🌐 Chung
                    </button>
                </nav>
            </div>

            {/* Tab Content */}
            <div className="mt-6">
                {activeTab === 'profile' && (
                    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 max-w-2xl">
                        <h2 className="text-lg font-semibold mb-4">Thông tin cá nhân</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
                                <input
                                    type="email"
                                    value={user?.email || ''}
                                    disabled
                                    className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-gray-500 sm:text-sm"
                                />
                            </div>

                            <div className="pt-4 border-t border-gray-100 dark:border-gray-800">
                                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Liên kết tài khoản</h3>
                                <div className="flex gap-3">
                                    <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800">
                                        <span className="text-xl">🪟</span> Microsoft Azure
                                    </button>
                                    <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800">
                                        <span className="text-xl">G</span> Google
                                    </button>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-gray-100 dark:border-gray-800">
                                <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                                    Đăng xuất khỏi tất cả thiết bị
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Bot tab content - Ẩn tạm thời, tập trung vào marketplace mini */}
                {/* {activeTab === 'bot' && (
                    <PersonaSettings />
                )} */}

                {activeTab === 'general' && (
                    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 max-w-2xl">
                        <h2 className="text-lg font-semibold mb-4">Cài đặt chung</h2>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Thông báo</h3>
                                    <p className="text-xs text-gray-500">Nhận email khi workflow hoàn thành</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" defaultChecked />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Giao diện</h3>
                                    <p className="text-xs text-gray-500">Chuyển đổi sáng/tối</p>
                                </div>
                                <select className="px-3 py-1 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-700">
                                    <option>Hệ thống</option>
                                    <option>Sáng</option>
                                    <option>Tối</option>
                                </select>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
