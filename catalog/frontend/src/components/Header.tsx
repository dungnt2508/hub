'use client';

import { useAuth } from '@/lib/auth-context';

export default function Header({ onMenuClick }: { onMenuClick: () => void }) {
    const { user, logout } = useAuth();

    return (
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-10">
            <div className="flex items-center gap-4">
                <button
                    onClick={onMenuClick}
                    className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 rounded-lg"
                >
                    ☰
                </button>
                <h2 className="text-lg font-semibold hidden sm:block text-gray-700 dark:text-gray-200">
                    Bảng điều khiển
                </h2>
            </div>

            <div className="flex items-center gap-4">
                {/* Notifications (Placeholder) */}
                <button className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full relative">
                    🔔
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                {/* User Menu */}
                <div className="flex items-center gap-3 pl-4 border-l border-gray-200 dark:border-gray-700">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user?.email}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Người dùng</p>
                    </div>
                    <button
                        onClick={logout}
                        className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                    >
                        Đăng xuất
                    </button>
                </div>
            </div>
        </header>
    );
}
